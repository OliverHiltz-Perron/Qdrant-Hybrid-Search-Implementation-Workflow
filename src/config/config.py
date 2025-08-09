"""
Shared configuration for modular pipeline
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - NEVER hardcode these!
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
JINA_API_KEY = os.environ.get("JINA_API_KEY")

# Validate API keys
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"
CHROMADB_PATH = BASE_DIR.parent / "chroma_documents_fixed"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Model settings
EMBEDDING_MODEL = "text-embedding-3-small"
GPT_MODEL = "gpt-4.1"  # Note: gpt-4-turbo, gpt-4o, and gpt-4o-mini support prompt caching
RERANKER_MODEL = "jina-reranker-v2-base-multilingual"

# Chunking settings
CHUNK_SIZE = 512  # tokens (max safe: 8000 for embeddings)
CHUNK_OVERLAP = 0.1  # 10% overlap
MIN_CHUNK_SIZE = 100  # minimum tokens per chunk
MAX_CHUNK_SIZE = 2000  # maximum tokens per chunk (embedding model limit)

# Search settings
INITIAL_SEARCH_RESULTS = 50
FINAL_SEARCH_RESULTS = 20
RERANKED_RESULTS = 20

# State mappings
STATE_MAPPINGS = {
    'AR': 'Arkansas', 'AZ': 'Arizona', 'CA': 'California', 'CO': 'Colorado',
    'CT': 'Connecticut', 'DC': 'District of Columbia', 'FL': 'Florida',
    'GA': 'Georgia', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky',
    'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland',
    'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota', 'MO': 'Missouri',
    'MS': 'Mississippi', 'MT': 'Montana', 'NC': 'North Carolina',
    'ND': 'North Dakota', 'NE': 'Nebraska', 'NH': 'New Hampshire',
    'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada', 'NY': 'New York',
    'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
    'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia',
    'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia',
    'WY': 'Wyoming'
}

# Collection name mappings
def get_collection_name(state_code):
    """Get ChromaDB collection name for a state"""
    return f"{state_code}_PreventionPlan"

# Logging configuration
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S',
    'level': 'INFO'
}

# BM25 Configuration
BM25_INDEX_DIR = OUTPUT_DIR / "bm25_indices"
BM25_K1 = 1.2  # Term frequency saturation parameter
BM25_B = 0.75  # Length normalization parameter
BM25_EPSILON = 0.25  # Floor value for IDF

# Hybrid Search Configuration
FUSION_K = 60  # RRF constant (for Reciprocal Rank Fusion)
DEFAULT_SEMANTIC_WEIGHT = 0.7
DEFAULT_BM25_WEIGHT = 0.3
HYBRID_TOP_K = 40  # Number of results to pass to reranker