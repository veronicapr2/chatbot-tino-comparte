import pytest

from rag.retriever import retrieve_context, load_chunks
from rag.vector_store import load_faiss_index
from rag.embeddings import load_embedding_model
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME
from rag.query_intent import normalize_text


QUERIES_EXPECTED = [
    # History / founders
    "¿Cómo nació Colombia Comparte?",
    "Cómo surgió la fundación",
    "Quién creó Colombia Comparte?",
    "Quiénes son los fundadores?",
    # EDIFICA / DESCUBRE
    "Qué es EDIFICA?",
    "Que es edifca?",  # typo
    "Qué es DESCUBRE?",
    # Mentorías / support
    "Cómo puedo recibir mentoría?",
    "Dónde encuentro mentorías?",
    # Conferences / services
    "Cómo puedo contratar una conferencia?",
    "Qué servicios ofrecen a empresas?",
    # Donations / support
    "Cómo puedo donar?",
    "Cómo puedo ayudar económicamente a la fundación?",
    # Platform / Tino / contact
    "Qué hace Tino?",
    "Cómo funciona la plataforma?",
    "Cuál es el impacto de la organización?",
    "Cómo me contacto con Colombia Comparte?",
]


@pytest.fixture(scope="module")
def rag_resources():
    chunks = load_chunks(CHUNKS_JSONL_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)
    return chunks, index, model


@pytest.mark.parametrize("q", QUERIES_EXPECTED)
def test_real_kb_queries_answerable(q, rag_resources):
    chunks, index, model = rag_resources
    norm = normalize_text(q)
    r = retrieve_context(norm, chunks, index, model)
    assert isinstance(r, dict)
    assert r.get("answerable") is True, f"Expected answerable for: {q} -- reason={r.get('reason')!r}"
