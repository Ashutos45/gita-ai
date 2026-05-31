# model.py

import os
import json
import threading

# =====================================
# Paths
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")
LABEL_MAP_PATH = os.path.join(MODEL_PATH, "label_mapping.json")


# =====================================
# Device Setup
# =====================================

device = None
torch = None

tokenizer = None
emotion_model = None
model_lock = threading.Lock()

id2label = {}
label2id = {}

def load_model_lazy():
    global tokenizer, emotion_model, device, torch
    if tokenizer is None or emotion_model is None:
        with model_lock:
            if tokenizer is None or emotion_model is None:
                print("[Lazy Load] Loading DistilBERT emotion model...")
                try:
                    import torch
                    from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
                    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
                    emotion_model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
                    emotion_model.to(device)
                    emotion_model.eval()
                    
                    if os.path.exists(LABEL_MAP_PATH):
                        with open(LABEL_MAP_PATH, "r") as f:
                            label_mapping = json.load(f)
                        label2id.update(label_mapping.get("label2id", {}))
                        id2label.update({int(k): v for k, v in label_mapping.get("id2label", {}).items()})
                    else:
                        id2label.update(emotion_model.config.id2label)
                        label2id.update(emotion_model.config.label2id)
                    print("[Lazy Load] DistilBERT loaded successfully.")
                except Exception as e:
                    raise RuntimeError(f"Failed to load emotion model: {e}")


# =====================================
# Utility: Get Raw Probabilities
# =====================================

def get_emotion_probabilities(text: str):
    """
    Returns raw probability tensor.
    Emotion logic handled in emotion.py
    """

    if not text or not text.strip():
        return None

    load_model_lazy()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=96
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = emotion_model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)

    return probs[0]