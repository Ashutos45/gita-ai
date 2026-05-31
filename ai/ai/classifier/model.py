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
                    import torch as _torch
                    from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
                    torch = _torch
                    device = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")

                    # Check if local fine-tuned weights exist
                    weights_file = os.path.join(MODEL_PATH, "model.safetensors")
                    pytorch_weights = os.path.join(MODEL_PATH, "pytorch_model.bin")
                    has_local_weights = os.path.isfile(weights_file) or os.path.isfile(pytorch_weights)

                    if has_local_weights:
                        print("[Lazy Load] Loading fine-tuned local model weights...")
                        tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
                        emotion_model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
                    else:
                        # Fallback: load base DistilBERT from HuggingFace Hub
                        # with our custom label config for 5 emotion classes
                        print("[Lazy Load] Local weights missing. Loading base DistilBERT from HuggingFace Hub...")
                        HF_BASE = "distilbert-base-uncased"
                        # Load label config from our config.json
                        if os.path.exists(LABEL_MAP_PATH):
                            with open(LABEL_MAP_PATH, "r") as f:
                                label_mapping = json.load(f)
                            _id2label = {int(k): v for k, v in label_mapping.get("id2label", {}).items()}
                            _label2id = label_mapping.get("label2id", {})
                        else:
                            _id2label = {0: "anger", 1: "confusion", 2: "fear", 3: "sadness", 4: "stress"}
                            _label2id = {"anger": 0, "confusion": 1, "fear": 2, "sadness": 3, "stress": 4}

                        from transformers import DistilBertConfig
                        config = DistilBertConfig.from_pretrained(
                            HF_BASE,
                            num_labels=len(_id2label),
                            id2label=_id2label,
                            label2id=_label2id,
                            problem_type="single_label_classification"
                        )
                        tokenizer = DistilBertTokenizerFast.from_pretrained(HF_BASE)
                        emotion_model = DistilBertForSequenceClassification.from_pretrained(
                            HF_BASE, config=config, ignore_mismatched_sizes=True
                        )
                        print("[Lazy Load] HuggingFace base model loaded (untuned — emotion classification will use keyword rules as primary signal).")

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