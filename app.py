"""
Ecode - Pure RAG GitHub Repository Explainer
Minimal Flask API with direct RAG pipeline
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from tools.github_loader import validate_github_url, get_repo_id, fetch_repo_files
from tools.vector_store import has_index, create_and_save_index, retrieve_similar
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ecode.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

# Ensure directories exist
Config.ensure_dirs()

# Initialize LLM
print("🔄 Initializing Ecode RAG system...")
Config.validate_api_key()
llm = ChatGoogleGenerativeAI(
    model=Config.LLM_MODEL,
    google_api_key=Config.GOOGLE_API_KEY,
    temperature=0
)
print("✅ System ready!")

# Generic query keywords for detection
GENERIC_KEYWORDS = [
    'explain', 'tell me about', 'what is', 'describe', 'give me', 
    'show me', 'overview', 'summary', 'about', 'inside', 'this repo',
    'this project', 'what does', 'how does', 'give the code'
]

def is_generic_query(question: str) -> bool:
    """Detect if a question is generic/vague."""
    question_lower = question.lower().strip()
    
    # Check for generic patterns
    if any(keyword in question_lower for keyword in GENERIC_KEYWORDS):
        # If question is very short or doesn't reference specific files/functions
        if len(question.split()) <= 5 or not any(char in question for char in ['.', '(', '/']):
            return True
    return False

# Specific RAG Prompt (for targeted questions - CODE AWARE)
SPECIFIC_RAG_PROMPT = """You are an expert software engineer explaining a GitHub repository.

**IMPORTANT**: The context contains ACTUAL CODE from repository files. When asked about code, SHOW the actual code snippets.

Rules:
- Use ONLY the provided context to answer
- Do NOT use outside knowledge or generate code
- If not found in context, respond: "Not found in this repository"
- **For code-based questions**:
  * **ALWAYS show the actual code snippets from the context** (copy verbatim, don't paraphrase)
  * Identify relevant files, functions, classes, and variables
  * Explain what the code DOES (behavior/functionality)
  * Trace logic flow and data transformations
  * Point out patterns, algorithms, or design decisions
- Use Markdown formatting:
  * **bold** for file names (**app.py**), functions (**fetch_data()**), classes
  * `inline code` for variables, parameters  
  * ```language code blocks for showing actual code (use proper language syntax highlighting)
  * Headings (##, ###) to organize
- When analyzing code:
  1. Identify WHICH file(s) contain the answer
  2. Show the ACTUAL CODE from the context (in a code block)
  3. Explain WHAT the code does
  4. Explain WHY it's structured that way (if patterns are clear)

Context (repository files):
{context}

User Question: {question}

Answer (show actual code from context):"""

# Generic/Fallback RAG Prompt (for vague questions)
GENERIC_RAG_PROMPT = """You are explaining a GitHub repository to a beginner.

The user's question is generic or unclear.

Rules:
- Use ONLY the provided repository context
- Do NOT use external knowledge  
- Provide a COMPREHENSIVE, DETAILED overview
- Use excellent Markdown formatting:
  * Use ## headings for main sections
  * Use **bold** for file names, technologies, and key terms
  * Use `code formatting` for technical terms and code snippets
  * Use bullet points and numbered lists
  * Include code examples where relevant
- Organize the answer into clear, detailed sections:
  
  ## 📋 Project Overview
  - What this repository is about (2-3 paragraphs)
  - Main purpose and use cases
  - Target audience
  
  ## 🛠️ Technologies & Stack
  - Programming languages used
  - Frameworks and libraries
  - Key dependencies
  
  ## 📁 Project Structure
  - Main files and directories
  - What each important file does
  - Configuration files
  
  ## ⚙️ How It Works
  - Core functionality explained
  - Workflow and architecture
  - Key algorithms or patterns used
  
  ## 🚀 Getting Started
  - Setup instructions (if available)
  - How to run the project
  - Common use cases

If any section cannot be answered from the context, state: "This information is not available in the retrieved files."

Context:
{context}

Provide a comprehensive, well-structured explanation with excellent formatting:

Answer:"""


@app.route('/')
def serve_index():
    """Serve the frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)


@app.route('/ask', methods=['POST'])
def ask_repo():
    """
    Main RAG endpoint
    Expects: { "repo_url": "...", "question": "..." }
    Returns: { "answer": "..." } or { "error": "..." }
    """
    data = request.json
    if not data or 'repo_url' not in data or 'question' not in data:
        return jsonify({"error": "Please provide both repo_url and question"}), 400

    repo_url = data['repo_url'].strip()
    question = data['question'].strip()

    if not repo_url or not question:
        return jsonify({"error": "repo_url and question cannot be empty"}), 400

    logger.info(f"Request: {repo_url} - {question}")

    try:
        # Step 1: Validate URL
        if not validate_github_url(repo_url):
            return jsonify({"error": "Invalid or unreachable GitHub URL"}), 400

        repo_id = get_repo_id(repo_url)

        # Step 2: Index repository if not already indexed
        if not has_index(repo_id):
            logger.info(f"Indexing new repository: {repo_id}")
            logger.info(f"Step 1/3: Fetching repository files...")
            docs = fetch_repo_files(repo_url, repo_id)
            if not docs:
                return jsonify({"error": "No readable files found in repository"}), 400
            logger.info(f"Step 2/3: Chunking {len(docs)} files...")
            logger.info(f"Step 3/3: Generating embeddings (this may take 10-30 seconds)...")
            create_and_save_index(repo_id, docs)
            logger.info(f"✅ Repository indexed successfully!")

        # Step 3: Retrieve relevant context
        context_docs = retrieve_similar(repo_id, question)
        if not context_docs:
            return jsonify({"answer": "Not found in this repository"}), 200

        # Step 4: Generate answer using RAG with file context
        # Include file paths in context for better code understanding
        context_parts = []
        for d in context_docs:
            file_info = f"File: {d.metadata.get('file_path', 'unknown')}"
            context_parts.append(f"{file_info}\n{d.page_content}")
        context_text = "\n\n---\n\n".join(context_parts)
        
        # Choose prompt based on query type
        if is_generic_query(question):
            logger.info(f"Detected generic query, using structured fallback")
            prompt = GENERIC_RAG_PROMPT.format(context=context_text)
        else:
            logger.info(f"Detected specific query, using targeted prompt")
            prompt = SPECIFIC_RAG_PROMPT.format(context=context_text, question=question)
        
        response = llm.invoke(prompt)
        answer = response.content

        return jsonify({"answer": answer})

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": "Something went wrong. Please try again later."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
