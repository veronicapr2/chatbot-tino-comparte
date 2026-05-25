from pathlib import Path
import os
from rag.config import CHUNKS_JSONL_PATH
from rag.retriever import load_chunks, build_kb_corpus, query_terms_absent_from_kb, unmatched_query_terms, semantic_search
from rag.embeddings import load_embedding_model
from rag.vector_store import load_faiss_index
from rag.query_intent import build_intent_query

os.environ['PYTHONPATH'] = str(Path.cwd() / 'src')

chunks = load_chunks(CHUNKS_JSONL_PATH)
index = load_faiss_index(Path('data/indexes/faiss_index.index'))
model = load_embedding_model('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

queries = [
    '¿De dónde salió la fundación?',
    'Estoy triste, pero quiero saber cómo me pueden ayudar con emprendimiento',
]

for q in queries:
    intent = build_intent_query(q)
    kb_corpus = build_kb_corpus(chunks)
    absent = query_terms_absent_from_kb(q, kb_corpus)
    print('QUERY:', q)
    print('INTENT:', intent)
    print('ABSENT:', absent)
    results = semantic_search(q, chunks, index, model, top_k=5, fetch_k=50)
    print('TOP RESULTS:')
    for res in results:
        print('  id', res['id'], 'score', res['score'], 'boost', res['boost'], 'final', res['final_score'], 'seccion', res['seccion'])
        print('   ', res['text'][:160].replace('\n', ' '))
    print('MISSING FOR TOP:', unmatched_query_terms(q, results[0], kb_corpus))
    print('---')
