"""Diagnóstico rápido de scores semánticos vs boost y alineación índice/chunks."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.config import (
    CHUNKS_JSON_PATH,
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    MIN_SCORE,
    WEAK_SCORE,
    MARGIN,
    MIN_BASE_SCORE,
    FALLBACK_MAX_SCORE,
)
from rag.embeddings import load_embedding_model
from rag.vector_store import load_faiss_index
from rag.retriever import load_chunks, semantic_search, should_answer

QUERIES = [
    "¿Qué es EDIFICA?",
    "¿Quién es un sarambabiche?",
    "¿Cuál es el nombre del perro del fundador?",
    "¿Cuánto cuesta ESTRUCTURA?",
]


def main() -> None:
    chunks = load_chunks(CHUNKS_JSON_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    print(f"Chunks: {len(chunks)} | Index ntotal: {index.ntotal}")
    if len(chunks) != index.ntotal:
        print("ADVERTENCIA: desalineación chunks <-> índice FAISS")

    review = sum(1 for c in chunks if c.get("validation_status") == "review")
    print(f"Chunks en review: {review}")

    print("\n=== Top-3 (score, boost, final, sección) ===")
    for query in QUERIES:
        results = semantic_search(query, chunks, index, model, top_k=3)
        print(f"\nQ: {query}")
        for row in results:
            seccion = row["seccion"][:60]
            print(
                f"  base={row['score']:.3f} boost={row['boost']:.2f} "
                f"final={row['final_score']:.3f} | {seccion}"
            )

    print("\n=== should_answer solo con score base (sin boost) ===")
    for query in QUERIES:
        results = semantic_search(query, chunks, index, model, top_k=5)
        base_only = [{**row, "final_score": row["score"]} for row in results]
        answerable = should_answer(
            base_only,
            MIN_SCORE,
            WEAK_SCORE,
            MARGIN,
            MIN_BASE_SCORE,
            FALLBACK_MAX_SCORE,
        )
        answerable_full = should_answer(
            results,
            MIN_SCORE,
            WEAK_SCORE,
            MARGIN,
            MIN_BASE_SCORE,
            FALLBACK_MAX_SCORE,
            query=query,
        )
        top_base = results[0]["score"] if results else 0.0
        second = results[1]["score"] if len(results) > 1 else 0.0
        print(
            f"{query!r}: base_only={answerable} with_boost={answerable_full} "
            f"top_base={top_base:.3f} margin_base={top_base - second:.3f}"
        )


if __name__ == "__main__":
    main()
