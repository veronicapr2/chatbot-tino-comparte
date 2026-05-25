from rag.chatbot import get_fixed_qa_answer
from rag.query_intent import build_intent_query, normalize_text
from rag.retriever import retrieve_context, load_chunks
from rag.vector_store import load_faiss_index
from rag.embeddings import load_embedding_model
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME


def test_fixed_answers_cover_common_reformulations():
    cases = {
        "De donde salio la fundacion?": ("perdida", "reconstruccion"),
        "Que programas tienen?": ("descubre", "estructura"),
        "Como puedo contratar una charla?": ("conferencias", "contacto"),
        "Que beneficios ofrece la organizacion?": ("mentorias", "acompanamiento"),
        "Que hacen por los emprendedores?": ("modelo", "negocio"),
        "A quienes ayudan?": ("pobreza oculta", "emprendedores"),
    }

    for query, expected_fragments in cases.items():
        answer = get_fixed_qa_answer(query)
        assert answer, query
        normalized = normalize_text(answer)
        assert all(fragment in normalized for fragment in expected_fragments)


def test_retrieval_still_rejects_out_of_kb_specific_fact():
    assert get_fixed_qa_answer("Cual es el nombre del perro del fundador?") is None

    chunks = load_chunks(CHUNKS_JSONL_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    result = retrieve_context(
        build_intent_query("Cual es el nombre del perro del fundador?"),
        chunks,
        index,
        model,
    )

    assert result["answerable"] is False
