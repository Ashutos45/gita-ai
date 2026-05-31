import re
from . import model


CONFIDENCE_THRESHOLD = 0.42
CLOSE_MARGIN = 0.06


# =====================================
# Keyword Emotion Signals (Weighted)
# =====================================

EMOTION_KEYWORDS = {
    "anger": ["angry", "furious", "rage", "hate", "annoyed"],
    "fear": ["afraid", "scared", "terrified", "fear", "panic"],
    "sadness": ["sad", "depressed", "cry", "hurt", "devastated"],
    "stress": ["pressure", "overwhelmed", "tired", "burnout"],
    "confusion": ["confused", "lost", "don't know", "uncertain"]
}

STRONG_WORDS = [
    "extremely", "terribly", "deeply",
    "very very", "so so", "too much"
]

NEGATION_PATTERNS = [
    r"\bnot\s+(\w+)",
    r"\bnever\s+(\w+)"
]


# =====================================
# Helpers
# =====================================

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _strong_intensity_boost(text: str) -> float:
    boost = 0.0
    for word in STRONG_WORDS:
        if word in text:
            boost += 0.05
    return min(boost, 0.15)


def _keyword_boost(text: str, scores: dict) -> None:
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for word in keywords:
            if word in text:
                scores[emotion] = scores.get(emotion, 0) + 0.06


def _handle_negation(text: str, scores: dict) -> None:
    """
    If negation detected like 'not happy'
    Reduce positive emotions, slightly boost sadness/confusion.
    """
    for pattern in NEGATION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            neg_word = match.group(1)

            # Reduce joy/positive signals
            if "joy" in scores:
                scores["joy"] *= 0.7
            if "neutral" in scores:
                scores["neutral"] *= 0.8

            # Boost sadness slightly
            if "sadness" in scores:
                scores["sadness"] += 0.05


def _normalize_scores(scores: dict) -> dict:
    total = sum(scores.values())
    if total == 0:
        return scores
    return {k: v / total for k, v in scores.items()}


# =====================================
# Ultra Smart Emotion Prediction
# =====================================

def predict_emotion(text: str) -> dict:

    if not text or not text.strip():
        return {"emotion": "confusion", "confidence": 0.5}

    text_clean = _normalize(text)

    # Trigger lazy load
    model.load_model_lazy()

    import torch
    import torch.nn.functional as F

    # -------- Model Prediction --------
    inputs = model.tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=96
    )

    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.emotion_model(**inputs)
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=-1)[0]

    model_scores = {
        model.id2label[i].strip().lower(): float(probabilities[i])
        for i in range(len(probabilities))
    }

    # -------- Keyword Boost --------
    _keyword_boost(text_clean, model_scores)

    # -------- Strong Word Boost --------
    intensity_boost = _strong_intensity_boost(text_clean)

    # -------- Negation Handling --------
    _handle_negation(text_clean, model_scores)

    # -------- Normalize Scores --------
    model_scores = _normalize_scores(model_scores)

    # -------- Sort --------
    sorted_emotions = sorted(
        model_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_emotion, top_conf = sorted_emotions[0]
    second_emotion, second_conf = sorted_emotions[1]

    # Apply intensity boost
    top_conf = min(top_conf + intensity_boost, 1.0)

    # -------- Smart Decision Rules --------
    if top_conf < CONFIDENCE_THRESHOLD:
        return {
            "emotion": "confusion",
            "confidence": round(top_conf, 4)
        }

    if abs(top_conf - second_conf) < CLOSE_MARGIN:
        return {
            "emotion": "confusion",
            "confidence": round(top_conf, 4)
        }

    if top_emotion in ["neutral", "joy"] and top_conf < 0.65:
        return {
            "emotion": "confusion",
            "confidence": round(top_conf, 4)
        }

    return {
        "emotion": top_emotion,
        "confidence": round(top_conf, 4),
        "secondary_emotion": second_emotion,
        "secondary_confidence": round(second_conf, 4)
    }