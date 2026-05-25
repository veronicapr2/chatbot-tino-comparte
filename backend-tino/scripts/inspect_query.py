import logging
from pathlib import Path
import os

os.environ['PYTHONPATH'] = str(Path.cwd() / 'src')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

from rag.retriever import load_chunks, retrieve_context
from rag.vector_store import load_faiss_index
from rag.embeddings import load_embedding_model
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME

chunks = load_chunks(CHUNKS_JSONL_PATH)
index = load_faiss_index(FAISS_INDEX_PATH)
model = load_embedding_model(EMBEDDING_MODEL_NAME)

queries = [
    'Cómo puedo recibir mentoría?',
    'Dónde encuentro mentorías?'
]

for q in queries:
    print('\n--- QUERY:', q)
    r = retrieve_context(q, chunks, index, model)
    print('ANSWERABLE:', r.get('answerable'), 'REASON:', r.get('reason'))
    print('TOP RESULTS:')
    for res in r.get('results', []):
        print('  id', res.get('id'), 'final', res.get('final_score'), 'score', res.get('score'), 'boost', res.get('boost'))
        print('   seccion:', res.get('seccion'))
        print('   text:', res.get('text')[:200].replace('\n',' '))
