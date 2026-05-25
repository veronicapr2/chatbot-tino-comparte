import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.config import (
    RAW_KB_PATH,
    PROCESSED_DIR,
    INDEX_DIR,
    CHUNKS_JSON_PATH,
    CHUNKS_JSONL_PATH,
    EMBEDDINGS_PATH,
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    MIN_WORDS,
    TARGET_WORDS,
    MAX_WORDS,
    OVERLAP_WORDS,
)
from rag.data_loader import ensure_directories, load_text_file
from rag.preprocessing import clean_text, split_sections, build_section_records
from rag.chunker import build_chunks
from rag.embeddings import load_embedding_model, create_embeddings
from rag.vector_store import create_faiss_index, save_faiss_index
from rag.retriever import save_chunks_json, save_chunks_jsonl


def main() -> None:
    ensure_directories(PROCESSED_DIR, INDEX_DIR)

    print("Cargando KB...")
    raw_text = load_text_file(RAW_KB_PATH)

    print("Limpiando texto...")
    cleaned_text = clean_text(raw_text)

    print("Separando secciones...")
    sections = split_sections(cleaned_text)
    print(f"Secciones detectadas: {len(sections)}")

    print("Extrayendo metadata...")
    section_records = build_section_records(sections)

    print("Creando chunks...")
    chunks = build_chunks(
        section_records=section_records,
        min_words=MIN_WORDS,
        target_words=TARGET_WORDS,
        max_words=MAX_WORDS,
        overlap_words=OVERLAP_WORDS,
    )

    chunks_to_review = [
        chunk for chunk in chunks
        if chunk["validation_status"] == "review"
    ]

    print(f"Chunks creados: {len(chunks)}")
    print(f"Chunks por revisar: {len(chunks_to_review)}")

    save_chunks_json(chunks, CHUNKS_JSON_PATH)
    save_chunks_jsonl(chunks, CHUNKS_JSONL_PATH)

    print(f"Chunks guardados en: {CHUNKS_JSON_PATH}")
    print(f"Chunks JSONL guardados en: {CHUNKS_JSONL_PATH}")

    print("Cargando modelo de embeddings...")
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    print("Generando embeddings...")
    embedding_texts = [chunk["embedding_text_enriched"] for chunk in chunks]
    embeddings = create_embeddings(embedding_texts, model)

    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"Embeddings guardados en: {EMBEDDINGS_PATH}")

    print("Creando índice FAISS...")
    index = create_faiss_index(embeddings)
    save_faiss_index(index, FAISS_INDEX_PATH)

    print(f"Índice FAISS guardado en: {FAISS_INDEX_PATH}")

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunk_count": len(chunks),
        "embedding_dim": int(embeddings.shape[1]),
        "index_vectors": int(index.ntotal),
        "chunks_review": len(chunks_to_review),
        "min_words": MIN_WORDS,
        "max_words": MAX_WORDS,
    }

    if manifest["chunk_count"] != manifest["index_vectors"]:
        raise RuntimeError(
            f"Desalineación: {manifest['chunk_count']} chunks vs "
            f"{manifest['index_vectors']} vectores en FAISS"
        )

    manifest_path = PROCESSED_DIR / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    print(f"Manifiesto guardado en: {manifest_path}")
    print("Proceso completado.")


if __name__ == "__main__":
    main()