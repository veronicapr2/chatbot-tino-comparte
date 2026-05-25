import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.config import (
    CHUNKS_JSON_PATH,
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    TOP_K,
    FETCH_K,
    MIN_SCORE,
    WEAK_SCORE,
    MARGIN,
    MIN_BASE_SCORE,
    FALLBACK_MAX_SCORE,
)
from rag.embeddings import load_embedding_model
from rag.vector_store import load_faiss_index
from rag.retriever import load_chunks
from rag.evaluation import (
    load_test_cases,
    evaluate_retrieval,
    evaluate_thresholds,
    evaluate_top_k,
)


def main() -> None:
    test_cases_path = PROJECT_ROOT / "tests" / "test_queries.json"

    chunks = load_chunks(CHUNKS_JSON_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)
    test_cases = load_test_cases(test_cases_path)

    print("\n=== Evaluación retrieval ===")
    df_eval = evaluate_retrieval(
        test_cases=test_cases,
        chunks=chunks,
        index=index,
        model=model,
        top_k=TOP_K,
        fetch_k=FETCH_K,
        min_score=MIN_SCORE,
        weak_score=WEAK_SCORE,
        margin=MARGIN,
        min_base_score=MIN_BASE_SCORE,
        fallback_max_score=FALLBACK_MAX_SCORE,
    )

    print(df_eval.to_string(index=False))
    print("\nAccuracy:", round(df_eval["correct"].mean(), 3))

    print("\n=== Evaluación thresholds ===")
    df_thresholds = evaluate_thresholds(
        test_cases=test_cases,
        chunks=chunks,
        index=index,
        model=model,
        thresholds=[0.25, 0.30, 0.35, 0.40, 0.45],
        top_k=TOP_K,
        fetch_k=FETCH_K,
    )

    print(df_thresholds.to_string(index=False))

    print("\n=== Evaluación top_k ===")
    df_top_k = evaluate_top_k(
        test_cases=test_cases,
        chunks=chunks,
        index=index,
        model=model,
        k_values=[1, 3, 5, 7],
        fetch_k=FETCH_K,
        min_score=MIN_SCORE,
    )

    print(df_top_k.to_string(index=False))

    failed = df_eval[df_eval["correct"] == False]

    if not failed.empty:
        print("\n=== Casos fallidos ===")
        print(failed.to_string(index=False))
    else:
        print("\nNo hay casos fallidos.")


if __name__ == "__main__":
    main()