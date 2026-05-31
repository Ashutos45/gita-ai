import numpy as np
import threading

# Lazy loaded
_model = None
_model_lock = threading.Lock()


def get_embedding(text: str) -> np.ndarray:
    """
    Convert text to normalized embedding vector.
    Returns float32 numpy array.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                print("[Lazy Load] Loading SentenceTransformer model...")
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer("all-MiniLM-L6-v2")
                print("[Lazy Load] SentenceTransformer loaded successfully.")

    embedding = _model.encode(text, normalize_embeddings=True)
    return np.array(embedding, dtype="float32")