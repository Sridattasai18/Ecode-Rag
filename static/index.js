/**
 * Ecode Frontend Logic
 * Handles user interactions and API communication
 */

// ===========================================
// DOM Elements
// ===========================================
const chatContainer = document.getElementById('chat-container');
const loadRepoBtn = document.getElementById('load-repo-btn');
const repoStatus = document.getElementById('repo-status');
const questionInput = document.getElementById('question-input');
const askBtn = document.getElementById('ask-btn');
const errorContainer = document.getElementById('error-container');
const errorMessage = document.getElementById('error-message');

let currentRepoUrl = null;

// ===========================================
// Utility Functions
// ===========================================

function showRepoStatus(message, type = 'info') {
    repoStatus.textContent = message;
    repoStatus.className = `status-message ${type}`;
    repoStatus.classList.remove('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');
}

function hideError() {
    errorContainer.classList.add('hidden');
}

function appendUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';
    msgDiv.textContent = text;
    chatContainer.appendChild(msgDiv);
    scrollToBottom();
}

function appendAIMessage(markdownText) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message';

    // Parse Markdown
    msgDiv.innerHTML = marked.parse(markdownText);

    // Highlight Code Blocks
    msgDiv.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    chatContainer.appendChild(msgDiv);
    scrollToBottom();
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setButtonLoading(button, isLoading, originalText = '') {
    if (isLoading) {
        button.disabled = true;
        // Keep original content if it was an icon, or set text
        if (!button.dataset.original) button.dataset.original = button.innerHTML;
        button.innerHTML = `<span class="loading-spinner"></span>`;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.original || originalText;
    }
}

// ===========================================
// API Functions
// ===========================================

async function askQuestion(repoUrl, question) {
    const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl, question: question })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Something went wrong.');
    return data;
}

// ===========================================
// Event Handlers
// ===========================================

async function handleLoadRepo() {
    const url = document.getElementById('repo-url').value.trim();
    if (!url) return showError('Please enter a GitHub repository URL.');

    hideError();

    // Show loading state
    showRepoStatus('Indexing repository…', 'loading');
    setButtonLoading(loadRepoBtn, true, 'Loading...');

    try {
        // Trigger indexing with a dummy question
        await askQuestion(url, 'What is this repository about?');

        currentRepoUrl = url;
        showRepoStatus('Repository loaded successfully!', 'success');

        chatContainer.classList.remove('hidden');
        questionInput.disabled = false;
        askBtn.disabled = false;
        questionInput.focus();

    } catch (error) {
        showError(error.message);
        showRepoStatus('Failed to load repository.', 'error');
    } finally {
        setButtonLoading(loadRepoBtn, false, 'Load');
    }
}

async function handleAskQuestion() {
    const question = questionInput.value.trim();
    if (!question || !currentRepoUrl) return;

    hideError();
    appendUserMessage(question);
    questionInput.value = '';

    // Auto-resize textarea back to 1 row
    questionInput.style.height = 'auto';

    setButtonLoading(askBtn, true);
    questionInput.disabled = true;

    try {
        const data = await askQuestion(currentRepoUrl, question);
        appendAIMessage(data.answer);
    } catch (error) {
        showError(error.message);
    } finally {
        setButtonLoading(askBtn, false);
        questionInput.disabled = false;
        questionInput.focus();
    }
}

// ===========================================
// Event Listeners
// ===========================================

loadRepoBtn.addEventListener('click', handleLoadRepo);

document.getElementById('repo-url').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleLoadRepo();
});

askBtn.addEventListener('click', handleAskQuestion);

questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleAskQuestion();
    }
});

// Auto-resize textarea
questionInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    hideError();
});

// Sidebar: New Repository Button
document.getElementById('new-chat-btn').addEventListener('click', () => {
    // Reset UI
    currentRepoUrl = null;
    document.getElementById('repo-url').value = '';
    questionInput.value = '';
    questionInput.disabled = true;
    askBtn.disabled = true;
    chatContainer.innerHTML = `
        <div class="message ai-message welcome-message">
            👋 <strong>Ready to explore!</strong><br>Enter a GitHub URL above to get started.
        </div>
    `;
    document.getElementById('repo-list').innerHTML = `
        <div class="repo-item active">
            <span class="repo-icon">📂</span>
            <span class="repo-name">New Repository</span>
        </div>
    `;
    showRepoStatus('', 'hidden');
    document.getElementById('repo-url').focus();
});
