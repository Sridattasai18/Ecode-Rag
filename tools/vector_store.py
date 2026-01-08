import os
import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import List, Tuple
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import Config

logger = logging.getLogger(__name__)

# Initialize embeddings model
_embeddings = None

# Language to extension mapping
LANGUAGE_MAP = {
    '.py': Language.PYTHON,
    '.js': Language.JS,
    '.ts': Language.TS,
    '.java': Language.JAVA,
    '.cpp': Language.CPP,
    '.c': Language.C,
    '.cs': Language.CSHARP,
    '.go': Language.GO,
    '.rs': Language.RUST,
    '.php': Language.PHP,
    '.rb': Language.RUBY,
    '.swift': Language.SWIFT,
    '.kt': Language.KOTLIN,
    '.scala': Language.SCALA,
    '.html': Language.HTML,
    '.md': Language.MARKDOWN,
    '.tex': Language.LATEX,
}

def get_embedding_model():
    """Lazily initialize the Gemini embeddings model."""
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY
        )
    return _embeddings

def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings using LangChain Gemini embeddings."""
    model = get_embedding_model()
    logger.info(f"Embedding {len(texts)} chunks...")
    embeddings = model.embed_documents(texts)
    return np.array(embeddings, dtype='float32')

def get_code_aware_splitter(file_extension: str) -> RecursiveCharacterTextSplitter:
    """
    Returns a code-aware splitter for the given file type.
    Falls back to generic splitter for unknown types.
    """
    language = LANGUAGE_MAP.get(file_extension.lower())
    
    if language:
        # Use language-specific splitter that respects code structure
        return RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
    else:
        # Generic text splitter for non-code files
        return RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True
        )

def chunk_documents(docs: List[Document]) -> List[Document]:
    """
    Splits documents into chunks with code-aware splitting.
    Groups documents by file extension for optimal chunking.
    """
    chunked_docs = []
    
    # Group docs by extension
    docs_by_ext = {}
    for doc in docs:
        ext = Path(doc.metadata.get('file_name', '')).suffix or '.txt'
        if ext not in docs_by_ext:
            docs_by_ext[ext] = []
        docs_by_ext[ext].append(doc)
    
    # Chunk each group with appropriate splitter
    for ext, ext_docs in docs_by_ext.items():
        splitter = get_code_aware_splitter(ext)
        chunks = splitter.split_documents(ext_docs)
        
        # Enrich metadata with chunk context
        for i, chunk in enumerate(chunks):
            # Add chunk info to help with retrieval
            chunk.metadata['chunk_index'] = i
            chunk.metadata['file_type'] = ext
            
            # Create a rich text representation for better embedding
            file_path = chunk.metadata.get('file_path', 'unknown')
            chunk.metadata['context_header'] = f"File: {file_path}\nType: {ext}"
            
        chunked_docs.extend(chunks)
    
    return chunked_docs

def get_index_path(repo_id: str) -> Tuple[Path, Path, Path]:
    base = Config.VECTOR_DB_PATH / repo_id
    base.mkdir(parents=True, exist_ok=True)
    return base / "index.faiss", base / "docs.pkl", base / "meta.json"

def has_index(repo_id: str) -> bool:
    index_path, docs_path, _ = get_index_path(repo_id)
    return index_path.exists() and docs_path.exists()

def create_and_save_index(repo_id: str, docs: List[Document]):
    """
    Creates embeddings for docs and saves FAISS index + doc store.
    """
    if not docs:
        logger.warning("No documents to index.")
        return

    logger.info(f"Chunking {len(docs)} documents with code-aware splitting...")
    chunks = chunk_documents(docs)
    logger.info(f"Generated {len(chunks)} chunks. Generating embeddings...")

    # Create enriched text for embedding (includes file path context)
    texts = []
    for chunk in chunks:
        context_header = chunk.metadata.get('context_header', '')
        # Embed with context for better retrieval
        enriched_text = f"{context_header}\n\n{chunk.page_content}"
        texts.append(enriched_text)
    
    embeddings = embed_texts(texts)
    
    # Initialize FAISS
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save
    index_path, docs_path, _ = get_index_path(repo_id)
    faiss.write_index(index, str(index_path))
    
    with open(docs_path, "wb") as f:
        pickle.dump(chunks, f)
        
    logger.info(f"Index for {repo_id} saved to {index_path}")

def retrieve_similar(repo_id: str, query: str, k: int = Config.TOP_K_RETRIEVAL) -> List[Document]:
    """
    Retrieves top k similar chunks for a query from the repo's index.
    """
    index_path, docs_path, _ = get_index_path(repo_id)
    
    if not index_path.exists():
        logger.error(f"Index not found for {repo_id}")
        return []
    
    index = faiss.read_index(str(index_path))
    
    with open(docs_path, "rb") as f:
        chunks = pickle.load(f)
        
    # Embed query using LangChain
    model = get_embedding_model()
    query_embedding = np.array([model.embed_query(query)], dtype='float32')
    distances, indices = index.search(query_embedding, k)
    
    results = []
    for idx in indices[0]:
        if idx < len(chunks) and idx >= 0:
            results.append(chunks[idx])
            
    return results
