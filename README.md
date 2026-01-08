# 🚀 Ecode - AI-Powered GitHub Repository Explainer

Ecode is an intelligent RAG (Retrieval-Augmented Generation) system that helps you understand any public GitHub repository through natural language questions. Built with a modern Spotify-inspired dark UI.

![Ecode Preview](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🔍 **Smart Code Analysis**: Advanced code-aware chunking that preserves function/class boundaries
- 💬 **Natural Language Queries**: Ask questions in plain English about any codebase
- 🎯 **Multi-Language Support**: Works with Python, JavaScript, Java, Go, Rust, C++, and 15+ languages
- 🎨 **Modern UI**: Beautiful Spotify-inspired dark theme with glassmorphism effects
- ⚡ **Fast Retrieval**: FAISS vector database for instant semantic search
- 🧠 **Context-Aware**: Understands code structure, not just text

## 🎬 Demo

1. Load any public GitHub repository
2. Ask questions like:
   - "How does authentication work?"
   - "Show me the main function"
   - "Explain the database schema"
   - "What APIs does this expose?"
3. Get detailed explanations with actual code snippets

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **AI/ML**: Google Gemini API, LangChain
- **Vector DB**: FAISS
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Markdown**: marked.js, highlight.js

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get it here](https://aistudio.google.com/app/apikey))
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Sridattasai18/Ecode-Rag.git
cd Ecode-Rag
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Gemini API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

**Get your API key**: https://aistudio.google.com/app/apikey

### 5. Run the Application

```bash
python app.py
```

The app will be available at: **http://127.0.0.1:5000**

## 📖 Usage

1. **Load a Repository**
   - Enter a public GitHub URL (e.g., `https://github.com/pallets/flask`)
   - Click "Load" and wait for indexing (first time only)

2. **Ask Questions**
   - "What is this repository about?"
   - "Show me the routing code"
   - "How does error handling work?"
   - "Display the database models"

3. **Get Detailed Answers**
   - File names and locations
   - Actual code snippets with syntax highlighting
   - Step-by-step explanations
   - Logic flow analysis

## 🏗️ Project Structure

```
Ecode/
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── static/
│   ├── index.html         # Frontend UI
│   ├── index.css          # Spotify-inspired styles
│   └── index.js           # Client-side logic
├── tools/
│   ├── github_loader.py   # Repo fetching & validation
│   ├── vector_store.py    # Code-aware chunking & indexing
│   └── __init__.py
├── vector_store/          # Indexed repositories (auto-created)
└── repos/                 # Cloned repositories (auto-created)
```

## 🔧 Configuration

Edit `config.py` to customize:

- **Chunk Size**: `CHUNK_SIZE = 1000` (default)
- **Retrieval Count**: `TOP_K_RETRIEVAL = 5` (default)
- **LLM Model**: `LLM_MODEL = "gemini-1.5-flash"` (default)
- **Embedding Model**: `EMBEDDING_MODEL = "models/text-embedding-004"`

## 💡 How It Works

1. **Repository Loading**
   - Validates and clones the GitHub repository
   - Extracts code from supported file types
   - Filters out binary files and build artifacts

2. **Code-Aware Chunking**
   - Uses language-specific splitters (Python, JS, Java, etc.)
   - Preserves function/class boundaries
   - Adds rich metadata (file path, type, context)

3. **Semantic Indexing**
   - Generates embeddings with Google's text-embedding-004
   - Stores in FAISS vector database
   - Cached for instant future queries

4. **Question Answering**
   - Retrieves relevant code chunks using semantic search
   - Passes context to Gemini with code-aware prompts
   - Returns formatted answers with code snippets

## 🎨 UI Features

- **Modern Dark Theme**: Inspired by Spotify's design language
- **Glassmorphism**: Blurred top bar with transparency
- **Smooth Animations**: Fade-ins, hover effects, micro-interactions
- **Responsive Design**: Works on desktop and mobile
- **Syntax Highlighting**: Powered by highlight.js

## 📊 Performance

- **Initial Indexing**: ~10-30 seconds per repository (one-time)
- **Query Response**: 2-5 seconds (depends on Gemini API)
- **Cache**: Indexed repositories persist across restarts

See [PERFORMANCE.md](PERFORMANCE.md) for detailed benchmarks.

## 🔒 Security

- ✅ `.env` file excluded from Git (API key protected)
- ✅ `.gitignore` configured for sensitive files
- ✅ No client-side API key exposure
- ✅ CORS enabled for local development only

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) for the powerful AI model
- [LangChain](https://langchain.com/) for RAG framework
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [Highlight.js](https://highlightjs.org/) for syntax highlighting

## 📧 Contact

**Developer**: Sridatta Sai  
**GitHub**: [@Sridattasai18](https://github.com/Sridattasai18)  
**Project Link**: [Ecode-Rag](https://github.com/Sridattasai18/Ecode-Rag)

---

⭐ **Star this repo** if you find it useful!
