import numpy as np
from sentence_transformers import SentenceTransformer


def load_embedding_model(model_name: str) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except TypeError:
        return SentenceTransformer(model_name)
    except Exception:
        return SentenceTransformer(model_name)


def create_embeddings(
    texts: list[str],
    model: SentenceTransformer,
    batch_size: int = 32,
    show_progress_bar: bool = True,
) -> np.ndarray:
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings.astype("float32")


def create_query_embedding(query: str, model: SentenceTransformer) -> np.ndarray:
    embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding.astype("float32")
