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

    # Paths (moved to user home to avoid Unicode issues on Windows)
    BASE_DIR = Path(__file__).parent
    ECODE_HOME = Path.home() / ".ecode"
    VECTOR_DB_PATH = ECODE_HOME / "vector_store"
    REPO_CACHE_DIR = ECODE_HOME / "repo_cache"
    
    # Retrieval
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 50
    TOP_K_RETRIEVAL = 5

    @classmethod
    def ensure_dirs(cls):
        cls.VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        cls.REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_api_key(cls):
        """Validates that the API key is set. Call this before LLM operations."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found. Please add it to your .env file.")

