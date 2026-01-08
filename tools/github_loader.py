import os
import shutil
import git
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.documents import Document
from config import Config

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', 'env', 
    'build', 'dist', 'target', 'bin', '.idea', '.vscode'
}
IGNORE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.mp4', 
    '.zip', '.tar', '.gz', '.pyc', '.exe', '.dll', '.so', '.dylib', '.class'
}

def _normalize_github_url(url: str) -> str:
    """
    Normalizes GitHub URL to root repository format.
    Strips /tree/branch/path, /blob/..., etc. to get the clone URL.
    
    Examples:
    - https://github.com/user/repo/tree/main/src -> https://github.com/user/repo
    - https://github.com/user/repo.git -> https://github.com/user/repo
    """
    url = url.rstrip("/").removesuffix(".git")
    
    # Strip path segments after repo name
    if "/tree/" in url or "/blob/" in url:
        url = url.split("/tree/")[0].split("/blob/")[0]
    
    return url

def validate_github_url(url: str) -> bool:
    """
    Validates if the URL is a reachable public GitHub repository.
    """
    if not url.startswith("https://github.com/"):
        logger.warning(f"Invalid URL format: {url}")
        return False
    
    # Normalize to root repo URL
    clean_url = _normalize_github_url(url)
    
    try:
        response = requests.head(clean_url, timeout=5)
        if response.status_code == 200:
            return True
        logger.warning(f"Repo not reachable (Status {response.status_code}): {url}")
        return False
    except Exception as e:
        logger.error(f"Error validating URL {url}: {e}")
        return False

def get_repo_id(url: str) -> str:
    """Generates a unique ID for the repo based on 'owner_repo'."""
    clean_url = _normalize_github_url(url)
    parts = clean_url.split("/")[-2:]
    return f"{parts[0]}_{parts[1]}"

def fetch_repo_files(url: str, repo_id: str) -> List[Document]:
    """
    Clones the repository and loads relevant text files.
    """
    repo_path = Config.REPO_CACHE_DIR / repo_id
    
    # Normalize URL to ensure git clone gets the root repository
    clone_url = _normalize_github_url(url)
    
    # If exists, pull strictly or re-clone? 
    # For now, to ensure clean state, we remove and re-clone if needed, 
    # but efficient way is to check existence.
    # User constraint: "Run ONCE per repository" (Handled by persistence check in graph).
    # If we are here, we assume we need to fetch.
    
    if repo_path.exists():
        logger.info(f"Repo cache found at {repo_path}, using existing files.")
    else:
        logger.info(f"Cloning {clone_url} to {repo_path}")
        try:
            git.Repo.clone_from(clone_url, repo_path, depth=1)
        except Exception as e:
            logger.error(f"Failed to clone repo: {e}")
            raise e

    docs = []
    
    for root, dirs, files in os.walk(repo_path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in IGNORE_EXTS:
                continue
                
            try:
                # Attempt to read as text
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if not content.strip():
                    continue
                
                rel_path = file_path.relative_to(repo_path)
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(rel_path),
                        "file_name": file,
                        "file_path": str(rel_path),
                        "repo_id": repo_id
                    }
                )
                docs.append(doc)
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
                continue
                
    logger.info(f"Loaded {len(docs)} files from {repo_id}")
    return docs
