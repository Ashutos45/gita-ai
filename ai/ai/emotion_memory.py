from collections import Counter
from typing import List, Dict


def analyze_emotion_trend(
    last_emotions: List[str],
    last_intensities: List[float] = None
) -> Dict:
    """
    Analyze emotional trend from recent emotions and intensities.
    Returns:
        dominant_emotion
        trend
        volatility
        escalation
    """

    if not last_emotions:
        return {
            "dominant_emotion": None,
            "trend": "stable",
            "volatility": 0.0,
            "escalation": False
        }

    counter = Counter(last_emotions)
    dominant = counter.most_common(1)[0][0]

    # -------------------------------
    # Basic Stability Check
    # -------------------------------

    trend = "stable"
    escalation = False

    if len(last_emotions) >= 3:

        last = last_emotions[-1]
        prev = last_emotions[-2]
        prev2 = last_emotions[-3]

        if last == prev == prev2:
            trend = "persistent"

        elif last != prev:
            trend = "shifting"

    # -------------------------------
    # Intensity-Based Escalation
    # -------------------------------

    volatility = 0.0

    if last_intensities and len(last_intensities) >= 3:

        recent = last_intensities[-3:]
        volatility = round(max(recent) - min(recent), 3)

        # Escalation if intensity increasing continuously
        if recent[2] > recent[1] > recent[0]:
            escalation = True
            trend = "worsening"

        # Recovery if intensity decreasing
        elif recent[2] < recent[1] < recent[0]:
            trend = "improving"

    return {
        "dominant_emotion": dominant,
        "trend": trend,
        "volatility": volatility,
        "escalation": escalation
    }