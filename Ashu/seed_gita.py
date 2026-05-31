import os
import pandas as pd

from Ashu.database import SessionLocal, engine, Base
import Ashu.models
from Ashu.models import Verse, VerseTranslation, Emotion
from Ashu.auto_map_emotions import auto_map

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Bhagwad_Gita", "Bhagwad_Gita.csv")


def seed_gita():
    print("Creating tables from metadata...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Loading CSV...")
    df = pd.read_csv(CSV_PATH)

    # Check if we already have verses in the database
    if db.query(Verse).first() is not None:
        print("Database already contains verses. Skipping verse seeding.")
    else:
        print("Inserting verses...")
        verses = []
        for _, row in df.iterrows():
            verse = Verse(
                chapter=int(row["Chapter"]),
                verse_number=int(row["Verse"]),
                sanskrit=row["Shloka"]
            )
            db.add(verse)
            verses.append((verse, row))
            
        db.commit() # Bulk commit verses to generate IDs
        
        print("Inserting translations...")
        for verse, row in verses:
            # English Translation
            if pd.notna(row["EngMeaning"]):
                db.add(
                    VerseTranslation(
                        verse_id=verse.id,
                        language="en",
                        meaning=row["EngMeaning"]
                    )
                )

            # Hindi Translation
            if pd.notna(row["HinMeaning"]):
                db.add(
                    VerseTranslation(
                        verse_id=verse.id,
                        language="hi",
                        meaning=row["HinMeaning"]
                    )
                )
        db.commit() # Commit all translations at once
        print("Verses and translations seeded successfully.")

    print("Seeding emotions...")
    emotions = [
        "anxiety",
        "fear",
        "confusion",
        "anger",
        "attachment",
        "sadness",
        "neutral",
        "desire",
        "stress",
        "hopelessness"
    ]

    for e in emotions:
        exists = db.query(Emotion).filter(Emotion.name == e).first()
        if not exists:
            db.add(Emotion(name=e))

    db.commit()
    db.close()
    print("Basic emotions seeded successfully.")
    
    print("Mapping emotions to verses...")
    auto_map()
    print("Seeding and mapping completed successfully.")


if __name__ == "__main__":
    seed_gita()