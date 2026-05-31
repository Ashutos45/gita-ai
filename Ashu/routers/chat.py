from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from Ashu.database import SessionLocal
from Ashu.models import Message, User, Verse
from Ashu.schemas import (
    MessageCreate,
    MessageResponse,
    ChatHistoryResponse,
    VerseResponse
)

from Ashu.auth import get_current_user

from ai.ai.engine import generate_reply

import os
import json
import requests
import httpx


router = APIRouter(prefix="/chat", tags=["chat"])


# =====================================
# Database Dependency
# =====================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================
# SAFE TEXT TRIM (FOR VOICE)
# =====================================

def safe_trim(text: str, limit: int = 1200):

    if not text:
        return ""

    if len(text) <= limit:
        return text

    trimmed = text[:limit]

    return trimmed.rsplit(" ", 1)[0]


# =====================================
# SEND MESSAGE
# =====================================

@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 1️⃣ Save user message
    user_msg = Message(
        user_id=current_user.id,
        sender="user",
        text=message.text
    )

    try:
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
    except Exception as e:
        db.rollback()
        print("[Database Error] Failed to save user message:", e)
        raise HTTPException(status_code=500, detail="Database transaction failed while saving user message.")

    # 2️⃣ Generate AI reply
    reply = generate_reply(message.text, user_id=current_user.id, db=db)

    # 🔧 Fix explanation type
    explanation = reply.get("explanation")

    if isinstance(explanation, dict):
        explanation = explanation.get("explanation", "")

    if explanation is None:
        explanation = ""

    emotion = reply.get("emotion")
    intensity = reply.get("intensity", 0.5)

    # 3️⃣ Update user message emotion
    try:
        user_msg.emotion = emotion
        user_msg.emotion_intensity = intensity
        db.commit()
    except Exception as e:
        db.rollback()
        print("[Database Error] Failed to update user message emotion:", e)

    # =====================================
    # Voice Generation (Optional)
    # =====================================

    audio_url = None

    if message.voice_mode and explanation:
        try:
            voice_text = safe_trim(
                (reply.get("meaning") or "") + " " + explanation,
                1200
            )

            tts_base_url = os.getenv("TTS_SERVICE_URL", "http://127.0.0.1:8001")
            async with httpx.AsyncClient() as client:
                voice_response = await client.post(
                    f"{tts_base_url}/speak",
                    params={"text": voice_text},
                    timeout=10.0
                )

                if voice_response.status_code == 200:
                    audio_file = voice_response.json().get("audio_file")
                    if audio_file:
                        audio_url = (
                            f"{tts_base_url}/generated_audio/{audio_file}"
                        )
        except Exception as e:
            print("Voice service error:", e)

    # =====================================
    # Save AI structured message
    # =====================================

    # Find verse in DB if exists to associate with the AI message
    verse_id = None
    if reply.get("chapter") and reply.get("verse_number"):
        v_db = db.query(Verse).filter(
            Verse.chapter == reply["chapter"],
            Verse.verse_number == reply["verse_number"]
        ).first()
        if v_db:
            verse_id = v_db.id

    ai_msg = Message(
        user_id=current_user.id,
        sender="ai",
        text=explanation,
        emotion=emotion,
        emotion_intensity=intensity,
        chapter=reply.get("chapter"),
        verse_number=reply.get("verse_number"),
        verse_id=verse_id
    )

    try:
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)
    except Exception as e:
        db.rollback()
        print("[Database Error] Failed to save AI response:", e)
        raise HTTPException(status_code=500, detail="Database transaction failed while saving AI reply.")

    # =====================================
    # Clean Response for Frontend
    # =====================================

    verse_response = VerseResponse(
        chapter=reply.get("chapter"),
        verse_number=reply.get("verse_number"),
        sanskrit=reply.get("sanskrit"),
        meaning=reply.get("meaning"),
        explanation=explanation
    )

    return MessageResponse(
        sender="ai",
        text=verse_response,
        emotion=emotion,
        timestamp=ai_msg.timestamp,
        audio_url=audio_url
    )


# =====================================
# CHAT HISTORY
# =====================================

@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    messages = db.query(Message).filter(
        Message.user_id == current_user.id
    ).order_by(Message.timestamp.asc()).all()

    history = []

    for msg in messages:

        if msg.sender == "ai":

            if msg.text.strip().startswith("{"):
                try:
                    parsed_data = json.loads(msg.text)
                    verse_obj = VerseResponse(
                        chapter=parsed_data.get("chapter"),
                        verse_number=parsed_data.get("verse_number"),
                        sanskrit=parsed_data.get("sanskrit"),
                        meaning=parsed_data.get("meaning"),
                        explanation=parsed_data.get("explanation") or ""
                    )
                except Exception:
                    verse_obj = VerseResponse(
                        chapter=None,
                        verse_number=None,
                        sanskrit=None,
                        meaning=None,
                        explanation=msg.text
                    )
            else:
                sanskrit = msg.verse.sanskrit if msg.verse else None
                meaning = None
                if msg.verse and msg.verse.translations:
                    en_trans = [t.meaning for t in msg.verse.translations if t.language == "en"]
                    meaning = en_trans[0] if en_trans else msg.verse.translations[0].meaning

                verse_obj = VerseResponse(
                    chapter=msg.chapter,
                    verse_number=msg.verse_number,
                    sanskrit=sanskrit,
                    meaning=meaning,
                    explanation=msg.text
                )

        else:

            verse_obj = VerseResponse(
                chapter=None,
                verse_number=None,
                sanskrit=None,
                meaning=None,
                explanation=msg.text
            )

        history.append(

            MessageResponse(
                sender=msg.sender,
                text=verse_obj,
                emotion=msg.emotion,
                timestamp=msg.timestamp,
                audio_url=None
            )

        )

    return {"messages": history}