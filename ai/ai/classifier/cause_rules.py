from typing import Dict, List
import re


# =====================================
# Global Cause Keyword Mapping
# (Not emotion-locked anymore)
# =====================================

CAUSE_KEYWORDS: Dict[str, List[str]] = {

    "relationship_issue": [
        "relationship", "breakup", "heartbreak",
        "girlfriend", "boyfriend", "partner",
        "love", "ex", "marriage"
    ],

    "career_confusion": [
        "career", "job", "promotion",
        "office", "work", "profession"
    ],

    "studies_failure": [
        "exam", "exams", "result", "results",
        "mark", "marks", "study", "studying",
        "college", "school", "assignment"
    ],

    "fear_of_disappointing": [
        "parent", "parents", "family",
        "expect", "expectation"
    ],

    "mental_pressure": [
        "pressure", "overwhelmed",
        "too much", "burden"
    ],

    "anger_ego": [
        "respect", "insult", "ego",
        "ignored", "hurt my pride"
    ],

    "hopelessness": [
        "give up", "hopeless",
        "empty", "worthless",
        "no point", "nothing matters"
    ],

    "loss_or_low_mood": [
        "lonely", "alone",
        "low", "sad", "down"
    ],

    "fear_general": [
        "future", "scared", "afraid"
    ]
}


# =====================================
# Default Cause by Emotion (Soft Bias)
# =====================================

DEFAULT_CAUSES = {
    "fear": "fear_general",
    "stress": "mental_pressure",
    "sadness": "loss_or_low_mood",
    "anger": "anger_ego",
    "confusion": "general"
}


# =====================================
# Helper Functions
# =====================================

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _count_matches(text: str, keywords: List[str]) -> int:
    count = 0
    for keyword in keywords:
        if keyword in text:
            count += 1
    return count


# =====================================
# Advanced Cause Detection
# =====================================

def detect_cause(text: str, emotion: str) -> str:

    text = _normalize(text)
    emotion = emotion.lower()

    scores = {}

    # Score each cause
    for cause_label, keywords in CAUSE_KEYWORDS.items():
        match_count = _count_matches(text, keywords)
        if match_count > 0:
            scores[cause_label] = match_count

    # If strong keyword match found
    if scores:
        # pick cause with highest match score
        return max(scores, key=scores.get)

    # If no keyword match → use emotion bias
    if emotion in DEFAULT_CAUSES:
        return DEFAULT_CAUSES[emotion]

    return "general"