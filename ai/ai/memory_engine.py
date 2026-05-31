# ai/ai/memory_engine.py

from collections import deque


class ConversationMemory:

    def __init__(self, window_size: int = 5):

        # Rolling history
        self.emotion_history = deque(maxlen=window_size)
        self.intensity_history = deque(maxlen=window_size)

        # Addiction tracking
        self.addiction_streak = 0

        # Spiritual progression score
        self.spiritual_score = 0

    # =====================================
    # EMOTION + INTENSITY UPDATE
    # =====================================

    def update(self, emotion: str, intensity: float, addiction_flag: bool = False):

        # Add to history
        self.emotion_history.append(emotion)
        self.intensity_history.append(intensity)

        trend = "stable"
        escalation = False
        volatility = 0.0
        persistent = False

        # -------------------------------
        # Emotion Persistence Check
        # -------------------------------

        if len(self.emotion_history) >= 3:
            last_three = list(self.emotion_history)[-3:]
            if last_three.count(last_three[0]) == 3:
                persistent = True

        # -------------------------------
        # Intensity Trend Check
        # -------------------------------

        if len(self.intensity_history) >= 3:

            last_three_int = list(self.intensity_history)[-3:]

            # Worsening
            if last_three_int[2] > last_three_int[1] > last_three_int[0]:
                trend = "worsening"
                escalation = True

            # Improving
            elif last_three_int[2] < last_three_int[1] < last_three_int[0]:
                trend = "improving"

        # -------------------------------
        # Volatility (Emotional Instability)
        # -------------------------------

        if len(self.intensity_history) >= 2:
            volatility = round(
                max(self.intensity_history) - min(self.intensity_history),
                3
            )

        # -------------------------------
        # Addiction Tracking
        # -------------------------------

        if addiction_flag:
            self.addiction_streak += 1
        else:
            self.addiction_streak = 0

        # -------------------------------
        # Spiritual Score Logic
        # -------------------------------

        if trend == "improving":
            self.spiritual_score += 1

        elif trend == "worsening":
            self.spiritual_score = max(0, self.spiritual_score - 1)

        # Bonus for breaking persistence
        if not persistent and trend == "improving":
            self.spiritual_score += 1

        return {
            "trend": trend,
            "persistent": persistent,
            "volatility": volatility,
            "escalation": escalation,
            "addiction_streak": self.addiction_streak,
            "spiritual_score": self.spiritual_score
        }

    # =====================================
    # Backward Compatibility
    # =====================================

    def update_emotion(self, emotion: str, intensity: float, addiction_flag: bool = False):
        return self.update(emotion, intensity, addiction_flag)

    def update_addiction(self, addiction_type=None):

        if addiction_type:
            self.addiction_streak += 1
        else:
            self.addiction_streak = 0

        return {
            "addiction_streak": self.addiction_streak
        }

    # =====================================
    # Reset Memory (New Session)
    # =====================================

    def reset(self):
        self.emotion_history.clear()
        self.intensity_history.clear()
        self.addiction_streak = 0
        self.spiritual_score = 0


def get_user_memory(db, user_id: int, window_size: int = 5) -> ConversationMemory:
    """
    Reconstructs the ConversationMemory state for a user from their database history.
    Filters out messages where emotion is None to exclude any message currently being processed.
    """
    from Ashu.models import Message

    mem = ConversationMemory(window_size=window_size)

    # Retrieve recent user messages in chronological order, excluding current unclassified message
    past_messages = (
        db.query(Message)
        .filter(
            Message.user_id == user_id,
            Message.sender == "user",
            Message.emotion.isnot(None)
        )
        .order_by(Message.timestamp.desc())
        .limit(20)  # Retrieve last 20 messages to calculate spiritual and addiction trends
        .all()
    )
    # Reverse to make them chronological
    past_messages.reverse()

    # Helper to check for addiction theme in message text
    def has_addiction_theme(text: str) -> bool:
        text_lower = text.lower() if text else ""
        addiction_words = [
            "addicted", "can't stop", "cannot stop", "compulsive", "again and again", "obsessed", "craving",
            "porn", "masturbation", "phone addiction", "scrolling", "social media addiction",
            "sex", "sexual", "lust", "physical desire", "horny"
        ]
        return any(word in text_lower for word in addiction_words)

    for msg in past_messages:
        addiction_flag = has_addiction_theme(msg.text)
        mem.update(
            emotion=msg.emotion or "confusion",
            intensity=msg.emotion_intensity or 0.5,
            addiction_flag=addiction_flag
        )

    return mem