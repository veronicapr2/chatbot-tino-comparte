"""Dry-run RAG: recupera contexto para preguntas y muestra los chunks más relevantes.
No carga LLM para evitar descargas pesadas; sirve para verificar recuperación y que respuestas
existentes en kb_final_colombia_comparte.txt sean recuperadas correctamente.
"""
from pathlib import Path
import os
os.environ['PYTHONPATH']=str(Path.cwd()/'src')
from rag.retriever import load_chunks, retrieve_context
from rag.embeddings import load_embedding_model
from rag.vector_store import load_faiss_index
from rag.config import CHUNKS_JSONL_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME

chunks = load_chunks(CHUNKS_JSONL_PATH)
index = load_faiss_index(FAISS_INDEX_PATH)
model = load_embedding_model(EMBEDDING_MODEL_NAME)

questions = [
    '¿Qué es Colombia Comparte?',
    '¿Cómo nació Colombia Comparte?',
    '¿Quiénes son sus fundadores?',
    '¿Qué es Edifica?',
    '¿Cómo puedo ayudar económicamente a la fundación?',
    '¿Cómo contratar una conferencia?',
    'Estoy triste, pero quiero saber cómo me pueden ayudar con emprendimiento',
    '¿De dónde salió la fundación?'
]

with open('results_retrieval.txt','w',encoding='utf-8') as f:
    for q in questions:
        r = retrieve_context(q, chunks, index, model, top_k=5, fetch_k=50)
        f.write('QUESTION: ' + q + '\n')
        f.write('ANSWERABLE: ' + str(r['answerable']) + ' REASON: ' + r.get('reason','') + '\n')
        if r['answerable']:
            f.write('RETRIEVED CONTEXT:\n')
            f.write(r['context'] + '\n')
        else:
            f.write('NO CONTEXT FOUND\n')
        f.write('\n' + ('-'*60) + '\n\n')

print('Dry run complete. Results in results_retrieval.txt')