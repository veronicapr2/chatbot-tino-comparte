from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.chatbot import ChatBot
from rag.query_intent import normalize_text


NO_INFO_PATTERNS = (
    "no tengo informacion",
    "no tengo informacion suficiente",
    "no encontre informacion",
    "no puedo responder con la informacion disponible",
    "no se",
    "no aparece en la base",
    "fuera de la base",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta ChatBot.ask sobre un dataset de preguntas.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", default="results_question_dataset.csv")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def has_no_info(answer: str) -> bool:
    normalized = normalize_text(answer)
    return any(pattern in normalized for pattern in NO_INFO_PATTERNS)


def contains_terms(answer: str, expected_terms: list[str]) -> bool:
    terms = [term for term in expected_terms if term]
    if not terms:
        return True
    normalized = normalize_text(answer)
    return all(normalize_text(term) in normalized for term in terms)


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]

    bot = ChatBot(max_new_tokens=180)
    bot.load()

    fieldnames = [
        "id", "category", "question", "should_answer", "answer", "no_info_detected",
        "contains_expected_terms", "status", "error",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True) if output_path.parent != Path(".") else None
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for item in rows:
            error = ""
            answer = ""
            no_info = False
            terms_ok = False
            status = "OK"
            try:
                question = item["question"]
                should_answer = bool(item.get("should_answer"))
                answer = bot.ask(question)
                no_info = has_no_info(answer)
                terms_ok = contains_terms(answer, item.get("expected_terms", []))

                if should_answer and no_info:
                    status = "FAIL_NO_INFO"
                elif should_answer and not terms_ok:
                    status = "REVIEW_EXPECTED_TOKEN"
                elif not should_answer and item.get("category") == "fuera_de_base" and not no_info:
                    status = "REVIEW_SHOULD_FALLBACK"
            except Exception as exc:
                status = "ERROR"
                error = f"{type(exc).__name__}: {exc}"

            writer.writerow({
                "id": item.get("id", ""),
                "category": item.get("category", ""),
                "question": item.get("question", ""),
                "should_answer": bool(item.get("should_answer")),
                "answer": re.sub(r"\s+", " ", answer).strip(),
                "no_info_detected": no_info,
                "contains_expected_terms": terms_ok,
                "status": status,
                "error": error,
            })

    print(f"Results written to {output_path} ({len(rows)} questions).")


if __name__ == "__main__":
    main()
