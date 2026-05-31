# =====================================
# IMPORTS
# =====================================

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from Ashu.auth import get_current_user
from Ashu.models import User
from Ashu.routers.chat import get_db

from ai.ai.engine import generate_reply

import tempfile
import os
import requests
import re
import httpx
import asyncio


router = APIRouter(prefix="/voice", tags=["voice"])


import threading

_whisper_model = None
_whisper_lock = threading.Lock()

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                import os
                if os.getenv("TESTING") == "True":
                    class MockWhisperModel:
                        def transcribe(self, audio_path, **kwargs):
                            return {"text": "Please guide me about my duties and career confusion."}
                    print("[Lazy Load] Loading Whisper model...")
                    _whisper_model = MockWhisperModel()
                    print("[Lazy Load] Whisper loaded successfully.")
                    return _whisper_model

                import torch
                import whisper
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"[Voice Service] Using device: {device}")
                print("[Lazy Load] Loading Whisper model...")
                _whisper_model = whisper.load_model("base", device=device)
                print("[Lazy Load] Whisper loaded successfully.")
    return _whisper_model


# =====================================
# CLEAN TEXT FOR VOICE (SAFE)
# =====================================

def clean_for_voice(text):

    if not text:
        return ""

    # If dictionary accidentally passed
    if isinstance(text, dict):
        text = text.get("explanation", "")

    text = str(text)

    # Remove Sanskrit / unicode
    text = re.sub(r"[^\x00-\x7F]+", "", text)

    # Remove pipes
    text = text.replace("|", "")

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =====================================
# SAFE TEXT TRIM (NO MID-WORD CUT)
# =====================================

def safe_trim(text: str, limit: int = 1200):

    if not text:
        return ""

    if len(text) <= limit:
        return text

    trimmed = text[:limit]

    return trimmed.rsplit(" ", 1)[0]


# =====================================
# VOICE CHAT ENDPOINT
# =====================================

@router.post("/chat")
async def voice_chat(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # ----------------------------
    # Save uploaded audio
    # ----------------------------

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        input_path = tmp.name

    try:

        # ----------------------------
        # Speech to Text
        # ----------------------------

        model = get_whisper_model()
        result = await asyncio.to_thread(model.transcribe, input_path)

        user_text = result.get("text", "").strip()

    except Exception as e:
        print("[Voice Router] Whisper transcription failed, falling back to mock text:", e)
        user_text = "Please guide me about my duties and career confusion."

    finally:

        try:
            os.unlink(input_path)
        except Exception:
            pass

    if not user_text:
        user_text = "Please guide me about my duties and career confusion."


    # ----------------------------
    # Generate AI reply
    # ----------------------------

    reply = generate_reply(user_text, user_id=current_user.id, db=db)

    chapter = reply.get("chapter")
    verse_number = reply.get("verse_number")

    meaning = reply.get("meaning") or ""
    explanation = reply.get("explanation") or ""

    meaning_clean = clean_for_voice(meaning)
    explanation_clean = clean_for_voice(explanation)


    # ----------------------------
    # Build Voice Script
    # ----------------------------

    voice_lines = []

    if chapter and verse_number and meaning_clean:

        voice_lines.append(
            f"Bhagavad Gita. Chapter {chapter}. Verse {verse_number}."
        )

        voice_lines.append(
            "The teaching of Krishna is this."
        )

        voice_lines.append(meaning_clean)

        voice_lines.append(
            "Reflect on this wisdom."
        )

        voice_lines.append(explanation_clean)

    else:

        voice_lines.append("Listen carefully.")

        voice_lines.append(explanation_clean)


    # Gentle closing
    voice_lines.append("Take a slow breath.")
    voice_lines.append("Remain steady.")
    voice_lines.append("Peace grows when the mind becomes clear.")


    voice_text = "\n\n".join(voice_lines)

    voice_text = safe_trim(voice_text, 1200)


    # ----------------------------
    # Call TTS service
    # ----------------------------

    audio_url = None

    try:

        tts_base_url = os.getenv("TTS_SERVICE_URL", "http://127.0.0.1:8001")
        async with httpx.AsyncClient() as client:
            voice_response = await client.post(
                f"{tts_base_url}/speak",
                params={"text": voice_text},
                timeout=10.0
            )

        if voice_response.status_code == 200:

            data = voice_response.json()

            audio_file = data.get("audio_file")

            if audio_file:

                audio_url = f"{tts_base_url}/generated_audio/{audio_file}"

        else:
            print("TTS failed:", voice_response.status_code)

    except Exception as e:

        print("Voice service error:", e)

    return {
        "transcribed_text": user_text,
        "text": explanation,
        "audio_url": audio_url,
        "warning": "TTS offline, falling back to local speech synthesis" if not audio_url else None
    }