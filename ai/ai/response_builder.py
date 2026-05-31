import random


# ==========================================
# 🕉 Greeting
# ==========================================

GREETING_MESSAGE = (
    "Welcome, Seeker.\n\n"
    "Speak freely — wisdom begins with honesty."
)


# ==========================================
# 🕉 Tone Variations
# ==========================================

OPENINGS_SOFT = [
    "I see what you are carrying within.",
    "Your heart feels unsettled, yet this is not weakness.",
    "You stand at a moment that requires clarity."
]

OPENINGS_STRONG = [
    "This confusion must not overpower you.",
    "Do not surrender to inner weakness.",
    "Stand firm and listen carefully."
]

CLOSINGS_SOFT = [
    "Act with steadiness. Peace will follow.",
    "Do your duty calmly. The rest will unfold.",
    "Walk forward without fear."
]

CLOSINGS_STRONG = [
    "Rise above this and act.",
    "Let discipline replace doubt.",
    "Stand firm and move forward."
]


# ==========================================
# 🚨 Crisis
# ==========================================

def crisis_response():
    return (
        "Your life is sacred.\n\n"
        "Do not make a permanent decision based on temporary pain.\n\n"
        "If you are in immediate danger, contact a trusted person immediately.\n\n"
        "You are not alone in this struggle."
    )


# ==========================================
# 🧘 Grounding
# ==========================================

def breathing_block():

    return (
        "Pause for a moment.\n\n"
        "Take a slow breath in for 4 seconds.\n"
        "Hold gently for 4 seconds.\n"
        "Release slowly for 6 seconds.\n\n"
        "Repeat this three times before continuing.\n\n"
    )


# ==========================================
# 🧠 Emotion Reflection
# ==========================================

def emotion_reflection(emotion: str):

    emotion = (emotion or "").lower()

    if emotion == "confusion":
        return (
            "Confusion arises when the mind demands certainty from an uncertain world.\n\n"
            "When too many possibilities appear before us, the mind begins to doubt its own strength.\n\n"
        )

    if emotion == "anxiety":
        return (
            "Anxiety appears when the mind travels too far into the future.\n\n"
            "Instead of focusing on the step before us, the mind imagines many outcomes and becomes restless.\n\n"
        )

    if emotion == "anger":
        return (
            "Anger clouds wisdom and weakens judgment.\n\n"
            "When the mind burns with reaction, clarity disappears.\n\n"
        )

    if emotion in ["sadness", "hopelessness"]:
        return (
            "Pain feels heavy, but it does not define your strength.\n\n"
            "Even in difficult moments, the inner self remains capable of renewal.\n\n"
        )

    if emotion == "fear":
        return (
            "Fear grows when we cling too tightly to imagined outcomes.\n\n"
            "The mind begins to create dangers that may never appear.\n\n"
        )

    if emotion == "desire":
        return (
            "Uncontrolled desire disturbs inner balance.\n\n"
            "When desire rules the mind, peace becomes difficult to maintain.\n\n"
        )

    if emotion == "joy":
        return (
            "Joy appears when the heart experiences harmony and connection.\n\n"
            "The Gita reminds us that true happiness grows when love is guided by wisdom rather than attachment.\n\n"
        )

    return "Peace returns when action aligns with responsibility.\n\n"


# ==========================================
# 📜 Verse Wisdom Explanation
# ==========================================

def verse_wisdom():

    return (
        "The Bhagavad Gita teaches that the mind becomes disturbed when it forgets its deeper purpose.\n\n"
        "Through wisdom and disciplined action, clarity gradually replaces confusion.\n\n"
        "When actions are performed sincerely without attachment to results, inner stability begins to grow.\n\n"
    )


# ==========================================
# 🧠 Personal Application
# ==========================================

def personal_application(emotion: str, cause: str):

    emotion = (emotion or "").lower()
    cause = (cause or "").lower()

    if cause == "career_confusion":
        return (
            "In matters of career, the mind often searches for a perfect path.\n\n"
            "But progress rarely begins with certainty.\n\n"
            "Instead, begin with sincere effort and allow experience to refine your direction.\n\n"
        )

    if cause == "studies_failure":
        return (
            "In your academic journey, fear of failure can become heavier than the work itself.\n\n"
            "The Gita reminds us that growth comes through disciplined effort, not constant worry about results.\n\n"
            "Focus on improving one step at a time.\n\n"
        )

    if cause == "relationship_issue":
        return (
            "In relationships, attachment often creates anxiety when we try to control how others feel.\n\n"
            "True connection grows through patience, honesty, and emotional balance.\n\n"
        )

    if cause == "fear_of_disappointing":
        return (
            "Your life is not meant to be lived only for approval.\n\n"
            "Act with sincerity rather than fear of judgment.\n\n"
        )

    if emotion == "anger":
        return (
            "Before reacting, pause and observe your thoughts.\n\n"
            "Control over the mind is far greater than control over others.\n\n"
        )

    if emotion in ["anxiety", "fear"]:
        return (
            "Bring your attention back to the present moment.\n\n"
            "The future becomes stable only when today's actions are clear and disciplined.\n\n"
        )

    if emotion in ["sadness", "hopelessness"]:
        return (
            "This phase does not define your destiny.\n\n"
            "Difficult seasons often prepare inner strength and deeper understanding.\n\n"
        )

    if emotion == "joy":
        return (
            "Moments of joy remind us that harmony is possible when actions align with inner values.\n\n"
            "Protect this balance with patience and gratitude.\n\n"
        )

    return (
        "Act with clarity rather than impulse.\n\n"
        "Steady effort transforms uncertainty into direction.\n\n"
    )


# ==========================================
# 🛠 Practical Guidance
# ==========================================

def practical_guidance():

    return (
        "Begin with small, steady steps.\n\n"
        "Focus on what you can improve today rather than worrying about distant outcomes.\n\n"
        "Discipline applied consistently becomes strength over time.\n\n"
    )


# ==========================================
# 🕉 MAIN RESPONSE BUILDER
# ==========================================

def build_response(result: dict, trend: dict = None, relapse: dict = None):

    if result.get("crisis"):
        return {
            "chapter": None,
            "verse_number": None,
            "sanskrit": None,
            "meaning": None,
            "explanation": crisis_response()
        }

    intent = result.get("intent")
    emotion = result.get("emotion")
    intensity = result.get("intensity", 0.5)
    verse = result.get("verse")
    cause = result.get("cause", "general")

    if intent == "greeting":
        return {
            "chapter": None,
            "verse_number": None,
            "sanskrit": None,
            "meaning": None,
            "explanation": GREETING_MESSAGE
        }

    mode = "gentle"

    if intensity >= 0.85:
        mode = "grounding"
    elif intensity >= 0.75:
        mode = "firm"

    if trend and trend.get("trend") == "worsening":
        mode = "grounding"

    opening = random.choice(OPENINGS_STRONG if mode == "firm" else OPENINGS_SOFT)
    closing = random.choice(CLOSINGS_STRONG if mode == "firm" else CLOSINGS_SOFT)

    explanation = ""

    if mode == "grounding":
        explanation += breathing_block()

    explanation += opening + "\n\n"
    explanation += emotion_reflection(emotion)
    explanation += verse_wisdom()
    explanation += personal_application(emotion, cause)
    explanation += practical_guidance()

    if relapse and relapse.get("addiction_streak", 0) > 1:
        explanation += (
            "You have encountered this pattern before.\n\n"
            "Now awareness must become discipline.\n\n"
        )

    explanation += closing

    return {
        "chapter": verse.get("chapter") if verse else None,
        "verse_number": verse.get("verse_number") if verse else None,
        "sanskrit": verse.get("sanskrit") if verse else None,
        "meaning": verse.get("meaning") if verse else None,
        "explanation": explanation
    }