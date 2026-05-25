from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "indexes"

RAW_KB_PATH = RAW_DIR / "kb_final_colombia_comparte.txt"

CHUNKS_JSON_PATH = PROCESSED_DIR / "chunks.json"
CHUNKS_JSONL_PATH = PROCESSED_DIR / "chunks.jsonl"
EMBEDDINGS_PATH = PROCESSED_DIR / "embeddings.npy"
FAISS_INDEX_PATH = INDEX_DIR / "faiss_index.index"

# Embeddings
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Chunking
MIN_WORDS = 35
FAQ_MIN_WORDS = 20
TARGET_WORDS = 140
MAX_WORDS = 240
OVERLAP_WORDS = 35

# Retrieval
TOP_K = 5
FETCH_K = 50

MIN_SCORE = 0.40
WEAK_SCORE = 0.32
MARGIN = 0.06
# Score semántico mínimo aunque haya boost por palabras clave (evita falsos positivos).
MIN_BASE_SCORE = 0.28
# Umbral por debajo del cual se considera consulta fuera de dominio (fallback estricto).
FALLBACK_MAX_SCORE = 0.36