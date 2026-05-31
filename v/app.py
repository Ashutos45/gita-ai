from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from TTS.api import TTS
import uuid
import os
import re
import torch

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

tts = TTS("tts_models/en/vctk/vits").to(device)

OUTPUT_DIR = os.path.join(BASE_DIR, "generated_audio")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount(
    "/generated_audio",
    StaticFiles(directory=OUTPUT_DIR),
    name="generated_audio"
)


def clean_text(text: str) -> str:
    text = re.sub(r'\d+\.\d+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@app.post("/speak")
def speak(text: str):

    clean = clean_text(text)

    file_name = f"{uuid.uuid4()}.wav"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    # Split long text safely
    sentences = re.split(r'(?<=[.!?]) +', clean)

    final_text = " ".join(sentences)

    tts.tts_to_file(
        text=final_text,
        speaker="p232",
        file_path=file_path,
        speed=0.92  # slightly slower for calm tone
    )

    return {
        "audio_file": file_name,
        "voice": "Male Calm (p232)",
        "device": device
    }