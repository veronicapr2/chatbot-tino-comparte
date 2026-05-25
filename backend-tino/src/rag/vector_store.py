from pathlib import Path

import faiss
import numpy as np


def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_faiss_index(index: faiss.IndexFlatIP, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))


def load_faiss_index(path: str | Path) -> faiss.Index:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el índice FAISS: {path}")

    return faiss.read_index(str(path))


def search_index(index: faiss.Index, query_embedding: np.ndarray, top_k: int):
    scores, indices = index.search(query_embedding, top_k)
    return scores[0], indices[0]