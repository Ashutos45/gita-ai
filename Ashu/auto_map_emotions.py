from Ashu.database import SessionLocal
from Ashu.models import Emotion, Verse, EmotionVerseMap
from sqlalchemy.exc import SQLAlchemyError


# =====================================
# Advanced Emotion → Verse Mapping
# =====================================

EMOTION_VERSE_MAP = {

    "anxiety": [
        (2, 47, 2.5),
        (2, 48, 3.0),
        (6, 5, 3.5),
        (18, 66, 2.0)
    ],

    "confusion": [
        (18, 63, 3.5),
        (4, 34, 2.5),
        (2, 50, 2.0)
    ],

    "anger": [
        (2, 62, 3.5),
        (16, 21, 3.0),
        (3, 37, 2.5)
    ],

    "sadness": [
        (2, 14, 3.0),
        (6, 20, 2.5),
        (12, 15, 2.5)
    ],

    "fear": [
        (4, 39, 3.0),
        (2, 56, 2.5),
        (16, 1, 2.0)
    ],

    "desire": [
        (3, 37, 3.5),
        (2, 62, 3.0),
        (16, 21, 2.5)
    ],

    "stress": [
        (2, 48, 3.0),
        (6, 26, 2.5),
        (18, 66, 2.0)
    ],

    "hopelessness": [
        (6, 5, 3.5),
        (2, 3, 3.0),
        (18, 66, 2.5)
    ],

    "neutral": [
        (2, 47, 2.0)
    ]
}


# =====================================
# Smart Auto Mapping Function
# =====================================

def auto_map():
    db = SessionLocal()

    try:
        for emotion_name, verse_list in EMOTION_VERSE_MAP.items():

            # ---------------------------------
            # Fetch or Create Emotion
            # ---------------------------------
            emotion = db.query(Emotion).filter(
                Emotion.name == emotion_name
            ).first()

            if not emotion:
                emotion = Emotion(name=emotion_name)
                db.add(emotion)
                db.commit()
                db.refresh(emotion)
                print(f"Created emotion: {emotion_name}")

            # ---------------------------------
            # Normalize Weights
            # ---------------------------------
            max_weight = max(weight for _, _, weight in verse_list)

            for chapter, verse_number, weight in verse_list:

                verse = db.query(Verse).filter(
                    Verse.chapter == chapter,
                    Verse.verse_number == verse_number
                ).first()

                if not verse:
                    print(f"Missing verse {chapter}.{verse_number}")
                    continue

                existing = db.query(EmotionVerseMap).filter(
                    EmotionVerseMap.emotion_id == emotion.id,
                    EmotionVerseMap.verse_id == verse.id
                ).first()

                # Normalize priority (0-1000 scale)
                normalized = weight / max_weight
                priority_value = int(normalized * 1000)

                if existing:
                    existing.weight = weight
                    existing.priority = priority_value
                    print(f"Updated {emotion_name} -> {chapter}.{verse_number}")
                else:
                    db.add(
                        EmotionVerseMap(
                            emotion_id=emotion.id,
                            verse_id=verse.id,
                            weight=weight,
                            priority=priority_value
                        )
                    )
                    print(f"Added {emotion_name} -> {chapter}.{verse_number}")

        db.commit()
        print("\nAdvanced emotion-to-verse mapping completed.")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    auto_map()