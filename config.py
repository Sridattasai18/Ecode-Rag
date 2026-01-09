import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Models
    LLM_MODEL = "gemini-flash-lite-latest"
    EMBEDDING_MODEL = "models/text-embedding-004"

    # Environment detection
    IS_VERCEL = os.getenv("VERCEL_ENV") is not None or os.getenv("VERCEL") is not None
    
    # Paths - Use /tmp on Vercel (ephemeral but writable), local paths otherwise
    BASE_DIR = Path(__file__).parent
    
    if IS_VERCEL:
        # Vercel serverless environment - use /tmp (ephemeral storage)
        ECODE_HOME = Path("/tmp/.ecode")
        VECTOR_DB_PATH = Path("/tmp/.ecode/vector_store")
        REPO_CACHE_DIR = Path("/tmp/.ecode/repo_cache")
        CHUNKS_DIR = Path("/tmp/.ecode/chunks")
    else:
        # Local development - use user home directory
        ECODE_HOME = Path.home() / ".ecode"
        VECTOR_DB_PATH = ECODE_HOME / "vector_store"
        REPO_CACHE_DIR = ECODE_HOME / "repo_cache"
        CHUNKS_DIR = ECODE_HOME / "chunks"
    
    # Retrieval
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 50
    TOP_K_RETRIEVAL = 5
    
    # API Settings
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    
    # Repository Settings
    MAX_REPO_SIZE_MB = 500  # Maximum repository size to clone
    FILE_TREE_MAX_DEPTH = 5  # Maximum depth for file tree traversal

    @classmethod
    def ensure_dirs(cls):
        cls.VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        cls.REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_api_key(cls):
        """Validates that the API key is set. Call this before LLM operations."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found. Please add it to your .env file.")

