# Ashu/routers/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
import json
import os
import asyncio
import websockets

from Ashu.database import SessionLocal
from Ashu.auth_utils import verify_token
from Ashu.models import User, Message, Verse
from ai.ai.engine import (
    get_gemini_client,
    get_verse_translation_with_fallback,
    QueryAnalysis,
    SeekerGuidance
)
from ai.ai.pipeline import gita_pipeline
from ai.ai.memory_engine import get_user_memory

router = APIRouter(prefix="/chat", tags=["websocket"])

async def stream_krishna_reply(websocket: WebSocket, text: str, user_id: int, db: Session):
    detected_lang = "en"
    english_query = text
    user_preferred_lang = "en"
    user_profile_summary = ""

    user_record = db.query(User).filter(User.id == user_id).first()
    if user_record:
        user_preferred_lang = user_record.preferred_language or "en"
        user_profile_summary = user_record.memory_summary or ""

    # 1. Detect language using Gemini (non-streamed)
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            analysis_instruction = (
                f"Analyze the user query. Detect if it is English (en), Hindi (hi), Sanskrit (sa), Tamil (ta), Telugu (te), or Odia (or). "
                "Return a JSON object matching the QueryAnalysis schema containing the 2-letter detected language code (lang) "
                "and the English translation of the query (translated_query). "
                f"If you cannot detect it confidently, set lang to '{user_preferred_lang}' and translated_query to the original query."
            )
            from google.genai import types
            analysis_response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model='gemini-2.5-flash',
                contents=f"User Query: '{text}'",
                config=types.GenerateContentConfig(
                    system_instruction=analysis_instruction,
                    response_mime_type="application/json",
                    response_schema=QueryAnalysis,
                    temperature=0.0,
                    http_options=types.HttpOptions(timeout=4.0)
                )
            )
            analysis = QueryAnalysis.model_validate_json(analysis_response.text)
            detected_lang = analysis.lang
            english_query = analysis.translated_query
            print(f"[WebSocket Stream] Detected language: {detected_lang}")
        except Exception as e:
            print("[WebSocket Stream] Language detection failed:", e)
            detected_lang = user_preferred_lang

    # 2. Run local intelligence pipeline
    result = await asyncio.to_thread(gita_pipeline, english_query)
    intent = result.get("intent")
    emotion = result.get("emotion")
    intensity = result.get("intensity", 0.5)
    verse = result.get("verse")
    addiction_flag = result.get("theme") == "self_control"

    if intent == "greeting":
        from ai.ai.response_builder import build_response
        reply = build_response(result=result)
        explanation = reply.get("explanation", "")
        await websocket.send_json({"event": "verse", "chapter": None, "verse_number": None, "sanskrit": None, "meaning": None})
        await websocket.send_json({"event": "text", "text": explanation})
        await websocket.send_json({"event": "end"})
        return

    if result.get("crisis"):
        from ai.ai.response_builder import build_response
        reply = build_response(result=result)
        explanation = reply.get("explanation", "")
        await websocket.send_json({"event": "verse", "chapter": None, "verse_number": None, "sanskrit": None, "meaning": None})
        await websocket.send_json({"event": "text", "text": explanation})
        await websocket.send_json({"event": "end"})
        return

    # 3. Verse selection & translation fallback
    if not verse:
        from ai.ai.engine import get_emotion_fallback_verse
        verse = get_emotion_fallback_verse(emotion)
    
    result["verse"] = verse
    translated_meaning = ""
    if verse and verse.get("id"):
        translated_meaning = get_verse_translation_with_fallback(db, verse["id"], detected_lang)
    elif verse:
        translated_meaning = verse.get("meaning") or ""

    if verse:
        verse["meaning"] = translated_meaning

    # Send grounding verse metadata to client first
    if verse:
        await websocket.send_json({
            "event": "verse",
            "chapter": verse.get("chapter"),
            "verse_number": verse.get("verse_number"),
            "sanskrit": verse.get("sanskrit"),
            "meaning": translated_meaning
        })

    # 4. Fetch memory trends
    user_memory = get_user_memory(db, user_id)
    memory_data = user_memory.update(emotion=emotion, intensity=intensity, addiction_flag=addiction_flag)
    
    # Save user message in DB
    user_msg = Message(user_id=user_id, sender="user", text=text, emotion=emotion, emotion_intensity=intensity)
    db.add(user_msg)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print("[Database Error] Failed to save user socket message:", e)

    # 5. Gemini streaming prompt setup
    gemini_success = False
    if gemini_client and verse:
        try:
            trend_str = memory_data.get("trend", "stable")
            relapse_str = "Seeker is showing a repeating pattern of struggle." if memory_data.get("addiction_streak", 0) > 1 else ""
            journey_level = memory_data.get("spiritual_score", 0)
            memory_str = f"Growth Journey Progress Level: {journey_level}. Volatility: {memory_data.get('volatility', 0.0)}."

            system_instruction = (
                "You are Lord Krishna, the divine teacher from the Bhagavad Gita. "
                "Counsel the Seeker in a warm, gentle, and authoritative tone, matching your character in the Gita. "
                "Write your guidance matching the target language: " + detected_lang + ".\n"
                "CRITICAL GROUNDING RULES:\n"
                "1. Use ONLY the retrieved grounding verse. Do NOT invent other verses.\n"
                "2. Never fabricate chapter or verse numbers.\n"
                "3. Never generate any Sanskrit text that is not provided in the Retrieved Grounding Verse.\n"
                "4. Stream your response naturally as a comforting speech block. Avoid raw JSON fields; explain the Gita wisdom, provide guidance, and list actionable alignment steps directly."
            )
            
            verse_text = f"Chapter {verse.get('chapter')}, Verse {verse.get('verse_number')}: {translated_meaning}"
            contents = f"""
            Retrieved Grounding Verse: {verse_text}
            Seeker Profile Context Summary: {user_profile_summary}
            Advisory Journey Tracking: {memory_str}
            Current Trend: {trend_str}
            {relapse_str}
            
            Seeker's Query (English Translation): "{text}"
            Primary Emotion: {emotion} (Intensity: {intensity})
            Target Output Language: {detected_lang}
            """
            
            from google.genai import types
            response_stream = gemini_client.models.generate_content_stream(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    http_options=types.HttpOptions(timeout=10.0)
                )
            )
            
            full_explanation_text = ""
            for chunk in response_stream:
                if chunk.text:
                    full_explanation_text += chunk.text
                    await websocket.send_json({"event": "text", "text": chunk.text})
            
            gemini_success = True
            
            # Save AI message in DB
            ai_msg = Message(
                user_id=user_id,
                sender="ai",
                text=full_explanation_text,
                emotion=emotion,
                emotion_intensity=intensity,
                chapter=verse.get("chapter"),
                verse_number=verse.get("verse_number"),
                verse_id=verse.get("id")
            )
            db.add(ai_msg)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print("[Database Error] Failed to save AI socket message:", e)

        except Exception as e:
            print("[WebSocket Stream] Gemini stream failed, applying fallback:", e)

    if not gemini_success:
        # Fallback to local response builder
        from ai.ai.response_builder import build_response
        reply = build_response(result=result, trend=memory_data, relapse=memory_data)
        explanation = reply.get("explanation", "")
        await websocket.send_json({"event": "text", "text": explanation})
        
        ai_msg = Message(
            user_id=user_id,
            sender="ai",
            text=explanation,
            emotion=emotion,
            emotion_intensity=intensity,
            chapter=verse.get("chapter") if verse else None,
            verse_number=verse.get("verse_number") if verse else None
        )
        db.add(ai_msg)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print("[Database Error] Failed to save fallback AI socket message:", e)

    await websocket.send_json({"event": "end"})


from pydantic import BaseModel
class ChatMessage(BaseModel):
    text: str

@router.post("/send")
async def chat_send_fallback(message: ChatMessage, token: str):
    print(f"[HTTP Fallback] Received message. Token: {token[:10]}...")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user_id = payload.get("user_id")
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=401, detail="User not found")
        
    # We create a dummy websocket-like object to catch the send_json calls
    class DummyWebSocket:
        def __init__(self):
            self.responses = []
        async def send_json(self, data):
            self.responses.append(data)
            
    dummy_ws = DummyWebSocket()
    await stream_krishna_reply(dummy_ws, message.text, user.id, db)
    db.close()
    
    return {"responses": dummy_ws.responses}

@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    print("[WebSocket] Connection attempt received at /ws")
    await websocket.accept()
    print("[WebSocket] Connection accepted")
    db = SessionLocal()
    user = None
    try:
        # Authentication
        token = websocket.query_params.get("token")
        print(f"[WebSocket] Token from query: {'Yes' if token else 'No'}")
        if not token:
            data = await websocket.receive_text()
            try:
                auth_data = json.loads(data)
                if auth_data.get("action") == "auth":
                    token = auth_data.get("token")
            except Exception:
                pass
        
        if not token:
            await websocket.send_json({"error": "Unauthorized: Missing token"})
            await websocket.close(code=4003)
            return

        payload = verify_token(token)
        print(f"[WebSocket] Token decoded successfully: {'Yes' if payload else 'No'}")
        if not payload:
            await websocket.send_json({"error": "Unauthorized: Invalid token"})
            await websocket.close(code=4003)
            return

        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        print(f"[WebSocket] User resolved: {user.full_name if user else 'No'}")
        if not user:
            await websocket.send_json({"error": "Unauthorized: User not found"})
            await websocket.close(code=4003)
            return

        await websocket.send_json({"status": "authenticated", "user": user.full_name})

        # Message loop
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_text = message_data.get("text", "").strip()
            if not user_text:
                continue

            await websocket.send_json({"event": "status", "text": "Krishna is contemplating…"})
            await stream_krishna_reply(websocket, user_text, user.id, db)

    except WebSocketDisconnect:
        print("[WebSocket] Seeker disconnected.")
    except Exception as e:
        print(f"[WebSocket Error] Exception occurred: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        db.close()


@router.websocket("/live")
async def voice_live_websocket(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    try:
        # Authentication
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json({"error": "Unauthorized: Missing token"})
            await websocket.close(code=4003)
            return

        payload = verify_token(token)
        if not payload:
            await websocket.send_json({"error": "Unauthorized: Invalid token"})
            await websocket.close(code=4003)
            return

        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.send_json({"error": "Unauthorized: User not found"})
            await websocket.close(code=4003)
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            await websocket.send_json({"error": "Gemini API key is not configured"})
            await websocket.close(code=4001)
            return

        # Connect to Gemini Live WebSocket API
        gemini_live_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
        
        print("[Gemini Live] Relaying socket connection...")
        async with websockets.connect(gemini_live_url) as gemini_ws:
            # Send setup configuration frame to Gemini
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.5-flash",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Puck"
                                }
                            }
                        }
                    },
                    "systemInstruction": {
                        "parts": [
                            {"text": "You are Lord Krishna, the divine spiritual mentor from the Bhagavad Gita. Speak with wisdom, empathy, and short guidance responses matching the seeker's current query and context summary."}
                        ]
                    }
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))
            
            # Wait for setup acknowledgment
            await gemini_ws.recv()
            await websocket.send_json({"status": "live", "user": user.full_name})

            # Relay task: Client -> Gemini
            async def client_to_gemini():
                try:
                    while True:
                        data = await websocket.receive()
                        if "bytes" in data:
                            # Send binary PCM input to Gemini Live API
                            pcm_data = data["bytes"]
                            import base64
                            encoded_pcm = base64.b64encode(pcm_data).decode("utf-8")
                            input_msg = {
                                "realtimeInput": {
                                    "mediaChunks": [
                                        {
                                            "mimeType": "audio/pcm;rate=16000",
                                            "data": encoded_pcm
                                        }
                                    ]
                                }
                            }
                            await gemini_ws.send(json.dumps(input_msg))
                        elif "text" in data:
                            # Handle potential text signals (e.g. stop, disconnect)
                            text_msg = data["text"]
                            try:
                                payload = json.loads(text_msg)
                                if payload.get("action") == "end":
                                    break
                            except Exception:
                                pass
                except Exception as e:
                    print("[Gemini Live] Error in client to gemini relay:", e)

            # Relay task: Gemini -> Client
            async def gemini_to_client():
                try:
                    async for message in gemini_ws:
                        resp = json.loads(message)
                        if "serverContent" in resp:
                            content = resp["serverContent"]
                            if "modelTurn" in content:
                                parts = content["modelTurn"]["parts"]
                                for part in parts:
                                    if "inlineData" in part:
                                        audio_base64 = part["inlineData"]["data"]
                                        import base64
                                        audio_bytes = base64.b64decode(audio_base64)
                                        # Send output audio bytes to seeker browser
                                        await websocket.send_bytes(audio_bytes)
                            if "turnComplete" in content:
                                await websocket.send_json({"event": "turn_complete"})
                except Exception as e:
                    print("[Gemini Live] Error in gemini to client relay:", e)

            await asyncio.gather(client_to_gemini(), gemini_to_client())

    except WebSocketDisconnect:
        print("[Gemini Live] Seeker disconnected.")
    except Exception as e:
        print(f"[Gemini Live Error] Exception occurred: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        db.close()
        try:
            await websocket.close()
        except Exception:
            pass
