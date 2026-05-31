import re
from typing import Dict, List


# =====================================
# Intent Rules (Weighted + Phrases)
# =====================================

INTENT_RULES: Dict[str, Dict[str, List[str]]] = {

    "mental_emotion": {
        "phrases": [
            "give up", "no hope", "feel empty"
        ],
        "keywords": [
            "sad", "depressed", "hopeless", "empty", "lonely",
            "afraid", "anxious", "panic", "stressed",
            "overwhelmed", "angry", "frustrated",
            "confused", "worthless"
        ]
    },

    "academic_career": {
        "phrases": [
            "career path", "exam result", "job interview"
        ],
        "keywords": [
            "exam", "result", "marks", "grades",
            "study", "college", "career",
            "job", "future", "interview"
        ]
    },

    "love_relationship": {
        "phrases": [
            "break up", "heart break"
        ],
        "keywords": [
            "love", "breakup", "heartbreak",
            "girlfriend", "boyfriend",
            "marriage", "divorce", "partner"
        ]
    },

    "devotion_spiritual": {
        "phrases": [
            "bhagavad gita", "spiritual path"
        ],
        "keywords": [
            "god", "krishna", "gita",
            "prayer", "faith",
            "meditation", "soul"
        ]
    }
}


CONFIDENCE_THRESHOLD = 1  # minimum score to accept


# =====================================
# Helpers
# =====================================

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _count_matches(text: str, keywords: List[str], weight: int = 1) -> int:
    score = 0
    for keyword in keywords:
        pattern = rf"\b{re.escape(keyword)}\b"
        if re.search(pattern, text):
            score += weight
    return score


# =====================================
# Advanced Intent Detection
# =====================================

def detect_intent(text: str) -> str:

    text = _normalize(text)

    scores = {}

    for intent, rule_set in INTENT_RULES.items():

        phrase_score = _count_matches(
            text,
            rule_set.get("phrases", []),
            weight=2  # phrases are stronger
        )

        keyword_score = _count_matches(
            text,
            rule_set.get("keywords", []),
            weight=1
        )

        total_score = phrase_score + keyword_score
        scores[intent] = total_score

    # Sort intents by score
    sorted_intents = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    best_intent, best_score = sorted_intents[0]

    # Tie handling
    if len(sorted_intents) > 1:
        second_score = sorted_intents[1][1]
        if best_score == second_score and best_score > 0:
            return "general_life"

    # Weak match fallback
    if best_score < CONFIDENCE_THRESHOLD:
        return "general_life"

    return best_intent