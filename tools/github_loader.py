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
        
        # Validate repository size before cloning (if possible via API)
        try:
            from .github_api import parse_github_url, GitHubAPI
            owner, repo = parse_github_url(url)
            api = GitHubAPI(timeout=Config.REQUEST_TIMEOUT)
            metadata = api.get_repo_metadata(owner, repo)
            
            # Check size (GitHub API returns size in KB)
            size_mb = metadata.get('size', 0) / 1024
            if size_mb > Config.MAX_REPO_SIZE_MB:
                logger.warning(f"Repository size ({size_mb:.1f}MB) exceeds limit ({Config.MAX_REPO_SIZE_MB}MB)")
                raise ValueError(
                    f"Repository is too large ({size_mb:.1f}MB). "
                    f"Maximum allowed size is {Config.MAX_REPO_SIZE_MB}MB. "
                    f"Please try a smaller repository."
                )
        except ImportError:
            logger.warning("Could not import github_api for size validation")
        except ValueError:
            raise  # Re-raise size validation errors
        except Exception as e:
            logger.warning(f"Could not validate repository size: {e}")
        
        # Clone with retry logic
        max_retries = Config.MAX_RETRIES
        for attempt in range(max_retries):
            try:
                logger.info(f"Cloning attempt {attempt + 1}/{max_retries}...")
                git.Repo.clone_from(clone_url, repo_path, depth=1)
                logger.info(f"✅ Successfully cloned repository")
                break
            except git.exc.GitCommandError as e:
                if "Repository not found" in str(e) or "not found" in str(e).lower():
                    logger.error(f"Repository not found or is private: {clone_url}")
                    raise ValueError("Repository not found or is private. Please check the URL.")
                elif attempt < max_retries - 1:
                    logger.warning(f"Clone failed (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to clone repository after {max_retries} attempts: {e}")
                    raise ValueError(f"Failed to clone repository: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during clone: {e}")
                raise ValueError(f"Failed to clone repository: {str(e)}")

    docs = []
    file_count = 0
    
    try:
        for root, dirs, files in os.walk(repo_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in IGNORE_EXTS:
                    continue
                    
                try:
                    # Attempt to read as text with size limit
                    file_size = file_path.stat().st_size
                    if file_size > 1_000_000:  # Skip files larger than 1MB
                        logger.debug(f"Skipping large file: {file_path.name} ({file_size / 1024:.1f}KB)")
                        continue
                    
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
                            "repo_id": repo_id,
                            "file_size": file_size
                        }
                    )
                    docs.append(doc)
                    file_count += 1
                    
                    # Log progress for large repositories
                    if file_count % 50 == 0:
                        logger.info(f"Processed {file_count} files...")
                        
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error walking repository directory: {e}")
        raise ValueError(f"Failed to read repository files: {str(e)}")
                
    logger.info(f"✅ Loaded {len(docs)} files from {repo_id}")
    
    if len(docs) == 0:
        raise ValueError("No readable files found in repository. The repository may be empty or contain only binary files.")
    
    return docs
