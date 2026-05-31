import faiss
import numpy as np
from sqlalchemy.orm import joinedload

from ai.ai.retrieval.embedder import get_embedding
from Ashu.database import SessionLocal
from Ashu.models import Verse


INDEX_PATH = "ai/ai/retrieval/gita_index.faiss"
META_PATH = "ai/ai/retrieval/verse_ids.npy"


# ==========================================
# 📥 Load All Verses with Translations
# ==========================================

def load_all_verses():
    db = SessionLocal()

    verses = (
        db.query(Verse)
        .options(joinedload(Verse.translations))  # prevent DetachedInstanceError
        .order_by(Verse.id)
        .all()
    )

    db.close()
    return verses


# ==========================================
# 🌍 Extract English Translation
# ==========================================

def extract_translation(verse):
    """
    Extract English meaning from VerseTranslation.
    """

    if not verse.translations:
        return ""

    # Prefer English translation
    for t in verse.translations:
        if t.language and t.language.lower() == "en":
            return t.meaning or ""

    # Fallback: first available translation
    return verse.translations[0].meaning or ""


# ==========================================
# 🧠 Normalize Vector (Cosine Similarity)
# ==========================================

def normalize_vector(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


# ==========================================
# 🔨 Build FAISS Index
# ==========================================

def build_index():
    verses = load_all_verses()

    print(f"🔄 Building embeddings for {len(verses)} verses...")

    embeddings = []
    verse_ids = []

    for verse in verses:
        translation_text = extract_translation(verse)

        # 🔥 Weight English more than Sanskrit for better matching
        combined_text = f"{translation_text} {translation_text} {verse.sanskrit or ''}".strip()

        if not combined_text:
            continue

        # Generate embedding
        vector = get_embedding(combined_text)

        # 🔥 Normalize vector (IMPORTANT for cosine similarity with IndexFlatIP)
        vector = normalize_vector(vector)

        embeddings.append(vector)
        verse_ids.append(verse.id)

    if not embeddings:
        print("❌ No embeddings generated.")
        return

    embeddings = np.vstack(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    # Using Inner Product (cosine similarity after normalization)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, INDEX_PATH)
    np.save(META_PATH, np.array(verse_ids))

    print("✅ Index built and saved successfully!")


# ==========================================
# 🚀 Run Builder
# ==========================================

if __name__ == "__main__":
    build_index()