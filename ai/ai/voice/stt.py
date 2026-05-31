# stt.py (Improved)

import sounddevice as sd
import numpy as np
import torch
from typing import Optional
from .voice_model import whisper_model


SAMPLE_RATE = 16000


def _normalize_audio(audio: np.ndarray) -> np.ndarray:
    max_val = np.max(np.abs(audio)) + 1e-9
    return audio / max_val


def listen_voice(duration: int = 6) -> Optional[str]:
    try:
        print("🎤 Listening... Speak clearly.")

        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32"
        )
        sd.wait()

        audio = audio.flatten()

        # Silence check
        if np.max(np.abs(audio)) < 0.01:
            print("⚠️ Audio too quiet.")
            return None

        audio = _normalize_audio(audio)
        audio = audio.astype(np.float32)

        result = whisper_model.transcribe(
            audio,
            fp16=torch.cuda.is_available(),
            task="transcribe"
        )

        text = result.get("text", "").strip()

        if not text:
            print("⚠️ No speech detected.")
            return None

        print("🗣 You said:", text)
        return text

    except Exception as e:
        print(f"Voice input error: {e}")
        return None