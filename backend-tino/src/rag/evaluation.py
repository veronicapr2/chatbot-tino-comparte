import json
from pathlib import Path

import pandas as pd

from .retriever import (
    build_kb_corpus,
    retrieve_context,
    semantic_search,
    should_answer,
)


def load_test_cases(path: str | Path) -> list[dict]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de pruebas: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_retrieval(
    test_cases: list[dict],
    chunks: list[dict],
    index,
    model,
    top_k: int = 5,
    fetch_k: int = 50,
    min_score: float = 0.40,
    weak_score: float = 0.32,
    margin: float = 0.06,
    min_base_score: float = 0.28,
    fallback_max_score: float = 0.36,
) -> pd.DataFrame:
    rows = []

    for case in test_cases:
        query = case["query"]
        expected = case.get("expected_section_contains")
        should_answer_expected = case.get("should_answer", expected is not None)

        retrieval = retrieve_context(
            query=query,
            chunks=chunks,
            index=index,
            model=model,
            top_k=top_k,
            fetch_k=fetch_k,
            min_score=min_score,
            weak_score=weak_score,
            margin=margin,
            min_base_score=min_base_score,
            fallback_max_score=fallback_max_score,
        )

        results = retrieval["results"]

        if results:
            top_result = results[0]
            top_section = top_result["seccion"]
            top_score = top_result["score"]
            top_final_score = top_result["final_score"]
        else:
            top_section = ""
            top_score = 0.0
            top_final_score = 0.0

        if not should_answer_expected:
            correct = retrieval["answerable"] is False
        else:
            correct = (
                retrieval["answerable"]
                and expected is not None
                and expected.lower() in top_section.lower()
            )

        rows.append({
            "query": query,
            "expected": expected,
            "should_answer_expected": should_answer_expected,
            "answerable": retrieval["answerable"],
            "top_section": top_section,
            "top_score": top_score,
            "top_final_score": top_final_score,
            "top_boost": top_result.get("boost", 0.0) if results else 0.0,
            "correct": correct,
            "reason": retrieval["reason"],
        })

    return pd.DataFrame(rows)


def evaluate_thresholds(
    test_cases: list[dict],
    chunks: list[dict],
    index,
    model,
    thresholds: list[float],
    top_k: int = 5,
    fetch_k: int = 50,
) -> pd.DataFrame:
    rows = []

    for threshold in thresholds:
        df_eval = evaluate_retrieval(
            test_cases=test_cases,
            chunks=chunks,
            index=index,
            model=model,
            top_k=top_k,
            fetch_k=fetch_k,
            min_score=threshold,
        )

        rows.append({
            "threshold": threshold,
            "accuracy": df_eval["correct"].mean(),
        })

    return pd.DataFrame(rows)


def evaluate_top_k(
    test_cases: list[dict],
    chunks: list[dict],
    index,
    model,
    k_values: list[int],
    fetch_k: int = 50,
    min_score: float = 0.40,
    weak_score: float = 0.32,
    margin: float = 0.06,
    min_base_score: float = 0.28,
    fallback_max_score: float = 0.36,
) -> pd.DataFrame:
    rows = []
    kb_corpus = build_kb_corpus(chunks)

    for k in k_values:
        top1_correct = 0
        recall_at_k = 0

        for case in test_cases:
            query = case["query"]
            expected = case.get("expected_section_contains")
            should_answer_expected = case.get("should_answer", expected is not None)

            results = semantic_search(
                query=query,
                chunks=chunks,
                index=index,
                model=model,
                top_k=k,
                fetch_k=fetch_k,
            )

            if not should_answer_expected:
                is_fallback = not should_answer(
                    results,
                    min_score=min_score,
                    weak_score=weak_score,
                    margin=margin,
                    min_base_score=min_base_score,
                    fallback_max_score=fallback_max_score,
                    query=query,
                    kb_corpus=kb_corpus,
                )
                top1_correct += int(is_fallback)
                recall_at_k += int(is_fallback)
                continue

            if not results or expected is None:
                continue

            top1_section = results[0]["seccion"]
            top1_is_correct = expected.lower() in top1_section.lower()

            any_correct_in_k = any(
                expected.lower() in result["seccion"].lower()
                for result in results
            )

            top1_correct += int(top1_is_correct)
            recall_at_k += int(any_correct_in_k)

        rows.append({
            "top_k": k,
            "top1_accuracy": top1_correct / len(test_cases),
            "recall_at_k": recall_at_k / len(test_cases),
        })

    return pd.DataFrame(rows)