import pytest

from rag.retriever import retrieve_context
from rag.query_intent import normalize_text
from rag.retriever import load_chunks
from rag.vector_store import load_faiss_index
from rag.embeddings import load_embedding_model
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME


QUERIES = [
    # origin / birthplace variants
    "Como nacio Colombia Comparte?",
    "De donde salio la fundacion?",
    "De donde salio la fundacion",
    "Como empezo Latinoamerica Comparte?",
    "Como surgio Colombia Comparte?",
    # founders variants
    "Quienes son sus fundadores?",
    "Quien fundo Colombia Comparte?",
    "quienes fundaron la fundacion",
    # typos / misspellings and business synonyms
    "Hablame sobre Edifica",
    "Cuentame de Edifica",
    "Que significa Edifica",
    "Que es Edifica?",
    "edifca",
    "me hablas de edifca",
    "Que es Edifca?",  # common typo
    "Que es la camar?",
    "Voya a hacer una donacion",
    "Ppor que no hay beca completa?",
    "Cuentame sobre Descubre",
    "Como puedo recibir mentoria",
    "Como puedo contratar una conferencia",
    "Como puedo donar",
    "Que servicios ofrecen a empresas",
    "Que es Tino",
    "Como puedo contratar una charla?",
    "Que beneficios ofrece la organizacion?",
]


@pytest.fixture(scope="module")
def rag_resources():
    chunks = load_chunks(CHUNKS_JSONL_PATH)
    index = load_faiss_index(FAISS_INDEX_PATH)
    model = load_embedding_model(EMBEDDING_MODEL_NAME)
    return chunks, index, model


@pytest.mark.parametrize("q", QUERIES)
def test_retrieval_answerable_for_synonyms(q, rag_resources):
    """Ensure retrieval returns an answerable=True for paraphrases/typos."""
    chunks, index, model = rag_resources
    norm = normalize_text(q)
    ctx = retrieve_context(norm, chunks, index, model)
    assert isinstance(ctx, dict), "retrieve_context must return a dict"
    assert ctx.get("answerable") is True, (
        f"Query not answerable: {q} -- norm={norm} -- reason={ctx.get('reason')!r}"
    )
