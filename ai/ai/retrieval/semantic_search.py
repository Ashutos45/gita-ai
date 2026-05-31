import numpy as np
import threading
from sqlalchemy.orm import joinedload

from ai.ai.retrieval.embedder import get_embedding
from Ashu.database import SessionLocal
from Ashu.models import Verse


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "gita_index.faiss")
META_PATH = os.path.join(BASE_DIR, "verse_ids.npy")


index = None
verse_ids = None
index_lock = threading.Lock()

def load_index_lazy():
    global index, verse_ids
    if index is None or verse_ids is None:
        with index_lock:
            if index is None or verse_ids is None:
                import faiss
                print("[Lazy Load] Loading FAISS index...")
                index = faiss.read_index(INDEX_PATH)
                verse_ids = np.load(META_PATH)
                print("[Lazy Load] FAISS index loaded successfully.")


def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """
    Normalize vector for cosine similarity stability.
    """
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def search(query: str, top_k: int = 5):
    """
    Pure semantic search.
    Returns list of verse dictionaries with raw similarity scores.
    """
    load_index_lazy()

    # -----------------------------------------
    # 1️⃣ Embed + Normalize Query
    # -----------------------------------------

    query_vector = get_embedding(query)
    query_vector = normalize_vector(query_vector)
    query_vector = np.expand_dims(query_vector, axis=0)

    # -----------------------------------------
    # 2️⃣ Search FAISS
    # -----------------------------------------

    scores, indices = index.search(query_vector, top_k)

    db = SessionLocal()
    results = []

    # -----------------------------------------
    # 3️⃣ Fetch Verses
    # -----------------------------------------

    for i in range(top_k):

        idx = indices[0][i]

        if idx == -1:
            continue

        verse_id = verse_ids[idx]

        verse = (
            db.query(Verse)
            .options(joinedload(Verse.translations))
            .filter(Verse.id == int(verse_id))
            .first()
        )

        if verse:

            english_meaning = ""

            for t in verse.translations:
                if t.language.lower() == "en":
                    english_meaning = t.meaning
                    break

            # Normalize score range (optional)
            similarity_score = float(scores[0][i])

            results.append({
                "id": verse.id,
                "chapter": verse.chapter,
                "verse_number": verse.verse_number,
                "sanskrit": verse.sanskrit,
                "meaning": english_meaning,
                "score": similarity_score
            })

    db.close()

    return results