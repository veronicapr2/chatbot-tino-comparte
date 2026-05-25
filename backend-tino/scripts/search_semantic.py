import argparse
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
from rag.retriever import (
    load_chunks,
    retrieve_context,
    query_terms_absent_from_kb,
    build_kb_corpus,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Búsqueda semántica sobre la KB (con decisión de fallback)."
    )
    parser.add_argument("query", help="Pregunta o consulta.")
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--fetch-k", type=int, default=FETCH_K)
    parser.add_argument("--preview-chars", type=int, default=0)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra candidatos aunque se active el fallback.",
    )
    return parser.parse_args()


def print_result(result: dict) -> None:
    print("=" * 80)
    print(f"Resultado {result['rank']}")
    print(f"Score base: {result['score']:.4f}")
    print(f"Boost: {result['boost']:.4f}")
    print(f"Score final: {result['final_score']:.4f}")
    print(f"Chunk: {result['id']}")
    print(f"Sección: {result['seccion']}")
    print(f"Categoría: {result['categoria']}")
    print(f"Query canonizado: {result['query_for_embedding']}")
    print()
    print(result["text"])
    print()


def main() -> None:
    args = parse_args()

    chunks = load_chunks(CHUNKS_JSON_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)
    kb_corpus = build_kb_corpus(chunks)

    retrieval = retrieve_context(
        query=args.query,
        chunks=chunks,
        index=index,
        model=model,
        top_k=args.top_k,
        fetch_k=args.fetch_k,
        min_score=MIN_SCORE,
        weak_score=WEAK_SCORE,
        margin=MARGIN,
        min_base_score=MIN_BASE_SCORE,
        fallback_max_score=FALLBACK_MAX_SCORE,
    )

    absent = query_terms_absent_from_kb(args.query, kb_corpus)

    print(f"Consulta: {args.query}")
    print(f"¿Responder?: {'Sí' if retrieval['answerable'] else 'No (fallback)'}")
    print(f"Motivo: {retrieval['reason']}")

    if absent:
        print(f"Términos no presentes en la KB: {', '.join(absent)}")

    if not retrieval["answerable"]:
        print()
        print("--- FALLBACK ---")
        print(
            "No se enviará contexto al modelo. "
            "Los resultados siguientes son solo diagnóstico."
        )
        candidates = retrieval["results"]
        if not args.debug:
            if candidates:
                top = candidates[0]
                print()
                print(
                    f"Candidato top (no usado): score base {top['score']:.4f}, "
                    f"final {top['final_score']:.4f} — {top['seccion']}"
                )
                print("Usa --debug para ver el ranking completo.")
            return

    results = retrieval["results"] if retrieval["answerable"] else retrieval["results"]

    if args.preview_chars:
        for result in results:
            text = result["text"].strip()
            if len(text) > args.preview_chars:
                result = {**result, "text": text[: args.preview_chars].rstrip() + "..."}

    for result in results:
        print_result(result)


if __name__ == "__main__":
    main()
