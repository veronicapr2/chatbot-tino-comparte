from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.chatbot import get_fixed_qa_answer, is_out_of_scope_query, should_force_fallback
from rag.conversational import resolve_conversational_response
from rag.humor import resolve_humor_response
from rag.input_understanding import analyze_user_input
from rag.query_intent import build_intent_query
from rag.retriever import enrich_query_for_embedding, load_chunks, retrieve_context
from rag.vector_store import load_faiss_index
from rag.embeddings import load_embedding_model
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audita rutas y recuperacion RAG sin cargar el LLM.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", default="results_dataset_audit.csv")
    return parser.parse_args()


def detect_route(question: str, fixed_answer: str | None, rag_answerable: bool) -> str:
    analysis = analyze_user_input(question)
    if analysis.is_greeting_only:
        return "casual_greeting"
    if analysis.is_standalone_emotion:
        return "emotion_only"
    if analysis.is_affection:
        return "casual_affection"
    if resolve_humor_response(question):
        return "humor"
    if resolve_conversational_response(question) and not analysis.route_hints.get("has_informational_question"):
        return "casual_conversation"
    normalized = build_intent_query(analysis.clean_query or question)
    if is_out_of_scope_query(normalized):
        return "out_of_scope"
    if should_force_fallback(normalized):
        return "forced_fallback"
    if fixed_answer:
        return "fixed_answer"
    if rag_answerable:
        return "rag"
    return "fallback"


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    output_path = Path(args.output)

    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    chunks = load_chunks(CHUNKS_JSONL_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    fieldnames = [
        "id", "category", "question", "should_answer", "detected_route",
        "normalized_query", "expanded_query", "fixed_answer_found", "rag_answerable",
        "top_section", "top_score", "top_chunk_preview", "status", "notes",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True) if output_path.parent != Path(".") else None
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for item in rows:
            try:
                question = item["question"]
                normalized = build_intent_query(question)
                expanded = enrich_query_for_embedding(normalized)
                fixed = get_fixed_qa_answer(question)
                retrieval = retrieve_context(normalized, chunks, index, model, top_k=5, fetch_k=80)
                top = retrieval["results"][0] if retrieval.get("results") else {}
                route = detect_route(question, fixed, bool(retrieval["answerable"]))

                should_answer = bool(item.get("should_answer"))
                status = "OK"
                if should_answer and not fixed and not retrieval["answerable"]:
                    status = "FAIL_RETRIEVAL_OR_ROUTE"
                elif should_answer and route in {"forced_fallback", "out_of_scope", "fallback"}:
                    status = "REVIEW_SHOULD_FALLBACK"
                elif should_answer and top and float(top.get("score", 0)) < 0.34 and not fixed:
                    status = "REVIEW_LOW_SCORE"
                elif fixed and retrieval["answerable"] is False:
                    status = "OK"
                elif not should_answer and retrieval["answerable"] and not fixed and item.get("category") == "fuera_de_base":
                    status = "REVIEW_SHOULD_FALLBACK"

                writer.writerow({
                    "id": item.get("id", ""),
                    "category": item.get("category", ""),
                    "question": question,
                    "should_answer": should_answer,
                    "detected_route": route,
                    "normalized_query": normalized,
                    "expanded_query": expanded.replace("\n", " | "),
                    "fixed_answer_found": bool(fixed),
                    "rag_answerable": bool(retrieval["answerable"]),
                    "top_section": top.get("seccion", ""),
                    "top_score": f"{float(top.get('score', 0)):.4f}" if top else "",
                    "top_chunk_preview": top.get("text", "")[:220].replace("\n", " "),
                    "status": status,
                    "notes": item.get("notes", ""),
                })
            except Exception as exc:
                writer.writerow({
                    "id": item.get("id", ""),
                    "category": item.get("category", ""),
                    "question": item.get("question", ""),
                    "should_answer": item.get("should_answer", ""),
                    "detected_route": "",
                    "normalized_query": "",
                    "expanded_query": "",
                    "fixed_answer_found": "",
                    "rag_answerable": "",
                    "top_section": "",
                    "top_score": "",
                    "top_chunk_preview": "",
                    "status": "ERROR",
                    "notes": f"{item.get('notes', '')} | {type(exc).__name__}: {exc}",
                })

    print(f"Audit written to {output_path} ({len(rows)} questions).")


if __name__ == "__main__":
    main()
