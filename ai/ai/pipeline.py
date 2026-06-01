# =====================================
# IMPORTS
# =====================================

import random

from .classifier.intent import detect_intent
from .classifier.emotion import predict_emotion
from .classifier.cause_rules import detect_cause

from ai.ai.retrieval.semantic_search import search


# =====================================
# THEME MAPPING
# =====================================

CAUSE_THEME_MAP = {
    "career_confusion": "karma_yoga",
    "studies_failure": "karma_yoga",
    "fear_of_disappointing": "bhakti",
    "mental_pressure": "karma_yoga",
    "anger_ego": "self_control",
    "hopelessness": "inner_peace",
    "loss_or_low_mood": "inner_peace",
    "fear_general": "bhakti",
    "relationship_issue": "bhakti",
    "general": "general"
}

INTENT_THEME_MAP = {
    "love_relationship": "bhakti",
    "devotion_spiritual": "bhakti",
    "general_life": "general"
}


# =====================================
# GREETING DETECTION
# =====================================

GREETING_KEYWORDS = [
    "hi", "hii", "hello", "hey",
    "namaste", "good morning",
    "good evening", "good afternoon"
]


def detect_greeting(text: str):
    return text.strip().lower() in GREETING_KEYWORDS


# =====================================
# CRISIS DETECTION
# =====================================

CRISIS_PATTERNS = [
    "end my life",
    "kill myself",
    "suicide",
    "want to die",
    "no reason to live",
    "don't want to live",
    "ending it",
    "life is pointless"
]


def detect_crisis(text: str):

    text_lower = text.lower()

    return any(pattern in text_lower for pattern in CRISIS_PATTERNS)


# =====================================
# RELATIONSHIP DETECTION
# =====================================

def detect_relationship_pattern(text: str):

    text = text.lower()

    if any(word in text for word in [
        "love", "relationship", "breakup",
        "heartbreak", "girlfriend",
        "boyfriend", "partner", "ex"
    ]):
        return "romantic_attachment"

    if any(word in text for word in [
        "sex", "sexual", "lust",
        "physical desire", "horny"
    ]):
        return "lust_desire"

    return "none"


# =====================================
# ADDICTION DETECTION
# =====================================

def detect_addiction(text: str):

    text = text.lower()

    if any(word in text for word in [
        "addicted", "can't stop",
        "cannot stop", "compulsive",
        "again and again", "obsessed",
        "craving"
    ]):
        return "general_addiction"

    if any(word in text for word in [
        "porn", "masturbation"
    ]):
        return "sexual_addiction"

    if any(word in text for word in [
        "phone addiction",
        "scrolling",
        "social media addiction"
    ]):
        return "dopamine_addiction"

    return "none"


# =====================================
# PSYCHOLOGICAL PATTERN
# =====================================

def detect_pattern(text: str):

    text = text.lower()

    if "what if" in text:
        return "future_anxiety"

    if "regret" in text or "mistake" in text:
        return "past_regret"

    if "parents" in text or "expect" in text:
        return "external_pressure"

    if "not good" in text or "not capable" in text:
        return "self_doubt"

    if "overthinking" in text:
        return "overthinking"

    return "general"


# =====================================
# INTENSITY ESTIMATION
# =====================================

def estimate_intensity(text: str):

    base = 0.4

    text_lower = text.lower()

    strong_words = [
        "very", "extremely", "too much",
        "cannot", "can't", "never",
        "always", "hopeless", "panic",
        "worthless", "terrified",
        "broken", "crying"
    ]

    for word in strong_words:

        if word in text_lower:
            base += 0.05

    base += min(text.count("!") * 0.05, 0.2)

    if len(text.split()) > 25:
        base += 0.05

    return min(base, 1.0)


# =====================================
# CORE PIPELINE
# =====================================

def gita_pipeline(text: str):

    if not text or not text.strip():

        return {
            "intent": "general_life",
            "emotion": "confusion",
            "cause": "general",
            "theme": "general",
            "intensity": 0.4,
            "confidence": 0.5,
            "crisis": False,
            "verse": None,
            "semantic_score": 0.0,
            "pattern": "general",
            "relationship_type": "none",
            "addiction_type": "none",
            "original_text": text
        }

    text = text.strip()


    # =====================================
    # GREETING
    # =====================================

    if detect_greeting(text):

        return {
            "intent": "greeting",
            "emotion": "neutral",
            "cause": "general",
            "theme": "general",
            "intensity": 0.3,
            "confidence": 1.0,
            "crisis": False,
            "verse": None,
            "semantic_score": 0.0,
            "pattern": "general",
            "relationship_type": "none",
            "addiction_type": "none",
            "original_text": text
        }


    # =====================================
    # CRISIS
    # =====================================

    if detect_crisis(text):

        return {
            "intent": "mental_emotion",
            "emotion": "sadness",
            "cause": "hopelessness",
            "theme": "inner_peace",
            "intensity": 1.0,
            "confidence": 1.0,
            "crisis": True,
            "verse": None,
            "semantic_score": 0.0,
            "pattern": "general",
            "relationship_type": "none",
            "addiction_type": "none",
            "original_text": text
        }


    # =====================================
    # AI CLASSIFICATION
    # =====================================

    import psutil
    import traceback
    
    print("[PIPELINE] START")

    intent = detect_intent(text)

    # Memory Check before Emotion
    mem_percent = psutil.virtual_memory().percent
    rss_mb = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"[Diagnostics] RAM Usage (Before Emotion): {rss_mb:.2f} MB ({mem_percent}%)")

    emotion_result = {"emotion": "confusion", "confidence": 0.5}
    try:
        if mem_percent > 80:
            print("[Diagnostics] RAM exceeds 80%. Skipping DistilBERT emotion classifier.")
            emotion_result = {"emotion": "anxiety", "confidence": 0.5}
        else:
            emotion_result = predict_emotion(text)
    except Exception as e:
        print(f"[Diagnostics] Emotion classification failed: {e}")
        traceback.print_exc()
        emotion_result = {"emotion": "anxiety", "confidence": 0.5}

    emotion = emotion_result.get("emotion", "confusion").strip().lower()
    confidence = round(float(emotion_result.get("confidence", 0.5)), 3)
    
    rss_mb = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"[Diagnostics] RAM Usage (After Emotion): {rss_mb:.2f} MB")
    print("[PIPELINE] EMOTION COMPLETE")


    # =====================================
    # TEXT BASED EMOTION BOOST
    # =====================================

    text_lower = text.lower()

    if any(w in text_lower for w in ["worry", "worried", "worries", "worrying"]):
        emotion = "anxiety"

    if any(w in text_lower for w in ["happy", "joy", "glad", "excited", "grateful"]):
        emotion = "joy"


    if confidence < 0.35 and emotion not in [
        "anxiety", "stress", "sadness",
        "fear", "desire", "anger", "joy"
    ]:
        emotion = "confusion"


    cause = detect_cause(text, emotion)

    relationship_type = detect_relationship_pattern(text)

    addiction_type = detect_addiction(text)

    pattern = detect_pattern(text)


    if relationship_type == "romantic_attachment":
        cause = "relationship_issue"


    # =====================================
    # THEME SELECTION
    # =====================================

    if addiction_type != "none":

        theme = "self_control"
        emotion = "desire"

    elif relationship_type == "romantic_attachment":

        theme = "bhakti"

        if emotion == "confusion":
            emotion = "sadness"

    elif relationship_type == "lust_desire":

        theme = "self_control"
        emotion = "desire"

    elif cause in CAUSE_THEME_MAP:

        theme = CAUSE_THEME_MAP.get(cause, "general")

    else:

        theme = INTENT_THEME_MAP.get(intent, "general")


    # =====================================
    # INTENSITY
    # =====================================

    rule_boost = estimate_intensity(text)

    confidence_boost = 0.4 + (confidence * 0.6)

    final_intensity = (rule_boost * 0.6) + (confidence_boost * 0.4)

    intensity = round(min(max(final_intensity, 0.2), 1.0), 2)


    # =====================================
    # SEMANTIC SEARCH
    # =====================================

    rss_mb = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"[Diagnostics] RAM Usage (Before Retrieval): {rss_mb:.2f} MB")

    semantic_query = f"{text} bhagavad gita {emotion} guidance"
    semantic_results = []
    
    try:
        semantic_results = search(semantic_query, top_k=5) or []
    except Exception as e:
        print(f"[Diagnostics] Semantic search failed: {e}")
        traceback.print_exc()

    verse = None
    best_score = 0.0

    if semantic_results:
        for result in semantic_results:
            score = float(result["score"])
            if score > best_score:
                best_score = score
                verse = result

    # =====================================
    # FALLBACK
    # =====================================

    if verse is None:
        fallback_query = f"bhagavad gita {emotion} wisdom"
        try:
            fallback = search(fallback_query, top_k=3)
            if fallback:
                verse = random.choice(fallback)
                best_score = 0.1
        except Exception as e:
            print(f"[Diagnostics] Fallback search failed: {e}")
            traceback.print_exc()
            
    rss_mb = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"[Diagnostics] RAM Usage (After Retrieval): {rss_mb:.2f} MB")
    print("[PIPELINE] RETRIEVAL COMPLETE")


    return {

        "intent": intent,
        "emotion": emotion,
        "cause": cause,
        "theme": theme,
        "intensity": intensity,
        "confidence": confidence,
        "crisis": False,
        "verse": verse,
        "semantic_score": round(best_score, 4),
        "pattern": pattern,
        "relationship_type": relationship_type,
        "addiction_type": addiction_type,
        "original_text": text

    }