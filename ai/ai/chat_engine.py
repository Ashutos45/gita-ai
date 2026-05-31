# =====================================
# CHAT ENGINE (MEMORY + PIPELINE + RESPONSE)
# =====================================

from ai.ai.pipeline import gita_pipeline
from ai.ai.response_builder import build_response
from ai.ai.memory_engine import ConversationMemory


# (Unused legacy code)


# =====================================
# MAIN CHAT FUNCTION
# =====================================

def chat(user_input: str) -> str:
    """
    Main chat interface.

    Flow:
        1. Run intelligence pipeline
        2. Crisis override check
        3. Update emotional memory
        4. Track addiction / relapse
        5. Build adaptive response
    """

    if not user_input or not user_input.strip():
        return "Speak freely. I am listening."

    # ---------------------------------
    # STEP 1 — Run Intelligence Engine
    # ---------------------------------

    result = gita_pipeline(user_input)

    # ---------------------------------
    # STEP 2 — Crisis Override (Highest Priority)
    # ---------------------------------

    if result.get("crisis"):
        return build_response(result=result)

    # ---------------------------------
    # STEP 3 — Emotional Trend Tracking
    # ---------------------------------

    trend_info = memory.update_emotion(
        emotion=result.get("emotion"),
        intensity=result.get("intensity", 0.5)
    )

    # ---------------------------------
    # STEP 4 — Addiction / Self-Control Tracking
    # ---------------------------------

    addiction_type = result.get("addiction_type", "none")

    # If self_control theme + desire emotion → addiction context
    if (
        result.get("theme") == "self_control"
        and result.get("emotion") == "desire"
    ):
        addiction_type = "general_addiction"

    relapse_info = memory.update_addiction(addiction_type)

    # ---------------------------------
    # STEP 5 — Relationship Pattern Tracking
    # ---------------------------------

    relationship_flag = result.get("relationship_type", "none")

    if relationship_flag != "none":
        memory.update_relationship_pattern(relationship_flag)

    # ---------------------------------
    # STEP 6 — Build Adaptive Response
    # ---------------------------------

    response = build_response(
        result=result,
        trend=trend_info,
        relapse=relapse_info
    )

    return response


# =====================================
# SESSION RESET
# =====================================

def reset_session():
    """
    Call this when starting a new user session.
    Clears conversation memory.
    """
    memory.reset()