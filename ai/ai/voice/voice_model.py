import torch
import whisper

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"🔊 Voice models loading on: {device}")

WHISPER_MODEL_SIZE = "base"

print(f"🎤 Loading Whisper model: {WHISPER_MODEL_SIZE}")

whisper_model = whisper.load_model(
    WHISPER_MODEL_SIZE,
    device=device
)

# Optional: Speed optimization for GPU
if device == "cuda":
    whisper_model = whisper_model.half()  # use FP16 on GPU

print("✅ Whisper loaded.")