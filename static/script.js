// API Base URL
const API_BASE_URL = 'http://localhost:5000';

// Conversation history
let conversationHistory = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    setupEventListeners();
});

function setupEventListeners() {
    // Send button click
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    
    // Enter key in input
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Modal close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMetricsForm();
        }
    });
    
    // Click outside modal to close
    document.getElementById('metricsModal').addEventListener('click', (e) => {
        if (e.target.id === 'metricsModal') {
            closeMetricsForm();
        }
    });
}

function checkHealth() {
    fetch(`${API_BASE_URL}/health`)
        .then(response => response.json())
        .then(data => {
            // Update ML status
            const mlStatus = document.getElementById('mlStatus');
            if (data.models_loaded) {
                mlStatus.textContent = `✓ ML Models: ${data.available_models.join(', ')}`;
                mlStatus.classList.add('active');
            } else {
                mlStatus.textContent = '⚠ ML Models: Not Loaded';
                mlStatus.classList.add('inactive');
            }
            
            // Update LLM status
            const llmStatus = document.getElementById('llmStatus');
            if (data.llm_enabled) {
                llmStatus.textContent = '✓ LLM: Ollama Enabled';
                llmStatus.classList.add('active');
            } else {
                llmStatus.textContent = '⚠ LLM: Rule-based Mode';
                llmStatus.classList.add('inactive');
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
            document.getElementById('mlStatus').textContent = '❌ ML Models: Error';
            document.getElementById('llmStatus').textContent = '❌ LLM: Error';
            document.getElementById('mlStatus').classList.add('inactive');
            document.getElementById('llmStatus').classList.add('inactive');
        });
}

function addMessage(content, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // Format message content
    const formattedContent = formatMessage(content);
    messageDiv.innerHTML = isUser ? `<p>${escapeHtml(content)}</p>` : formattedContent;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessage(content) {
    let formatted = content
        // Bold text **text**
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Headers ### Header or ## Header
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h3>$1</h3>')
        // Code blocks `code`
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Line breaks
        .replace(/\n/g, '<br>');
    
    // Wrap lists properly
    const lines = formatted.split('<br>');
    let inList = false;
    const processedLines = [];
    
    for (let line of lines) {
        if (/^(\d+\.|[•\-\*])\s/.test(line)) {
            if (!inList) {
                processedLines.push('<ul>');
                inList = true;
            }
            // Remove bullet/number and wrap in li
            line = line.replace(/^(\d+\.|[•\-\*])\s/, '');
            processedLines.push(`<li>${line}</li>`);
        } else {
            if (inList) {
                processedLines.push('</ul>');
                inList = false;
            }
            if (line.trim()) {
                processedLines.push(line);
            }
        }
    }
    
    if (inList) {
        processedLines.push('</ul>');
    }
    
    formatted = processedLines.join('<br>');
    return formatted;
}

function sendSuggestion(text) {
    document.getElementById('chatInput').value = text;
    sendMessage();
}

function quickPredict() {
    const sample = {
        sales: 25000,
        expenses: 12000,
        marketing_spend: 2500
    };
    
    const message = `Predict my profit with sales of $${sample.sales}, expenses of $${sample.expenses}, marketing spend of $${sample.marketing_spend}`;
    sendSuggestion(message);
}

function openMetricsForm() {
    document.getElementById('metricsModal').classList.remove('hidden');
}

function closeMetricsForm() {
    document.getElementById('metricsModal').classList.add('hidden');
    document.getElementById('metricsForm').reset();
}

function submitMetrics(event) {
    event.preventDefault();
    
    const sales = parseFloat(document.getElementById('salesInput').value) || 20000;
    const expenses = parseFloat(document.getElementById('expensesInput').value) || 10000;
    const marketing = parseFloat(document.getElementById('marketingInput').value) || 2000;
    const employees = parseInt(document.getElementById('employeesInput').value) || 20;
    const competition = parseInt(document.getElementById('competitionInput').value) || 3;
    
    const message = `I have a startup with monthly sales of $${sales}, expenses of $${expenses}, marketing spend of $${marketing}, ${employees} employees, and competition level of ${competition}. What is my profit forecast and what recommendations do you have?`;
    
    closeMetricsForm();
    sendSuggestion(message);
}

function clearChat() {
    if (confirm('Clear all chat messages?')) {
        document.getElementById('chatMessages').innerHTML = `
            <div class="message bot-message welcome-message">
                <div class="message-content">
                    <h2>👋 Chat Cleared</h2>
                    <p>Ready for a fresh conversation!</p>
                </div>
            </div>
        `;
        conversationHistory = [];
    }
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, true);
    chatInput.value = '';
    chatInput.focus();
    
    // Disable send button
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    loadingDiv.id = 'loadingMessage';
    loadingDiv.innerHTML = '<p class="loading">💭 Analyzing your business metrics...</p>';
    document.getElementById('chatMessages').appendChild(loadingDiv);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        // Send message to backend
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory
            })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        const loadingMsg = document.getElementById('loadingMessage');
        if (loadingMsg) loadingMsg.remove();
        
        if (response.ok) {
            // Add bot response
            addMessage(data.response, false);
            
            // Update conversation history
            conversationHistory.push({
                user: message,
                bot: data.response
            });
            
            // Keep history limited to last 20 messages
            if (conversationHistory.length > 20) {
                conversationHistory = conversationHistory.slice(-20);
            }
        } else {
            const loadingMsg = document.getElementById('loadingMessage');
            if (loadingMsg) loadingMsg.remove();
            addMessage(`❌ Error: ${data.error || 'Unknown error occurred'}`, false);
        }
    } catch (error) {
        const loadingMsg = document.getElementById('loadingMessage');
        if (loadingMsg) loadingMsg.remove();
        addMessage('❌ Error: Failed to connect to server. Make sure the Flask backend is running on port 5000.', false);
        console.error('Error:', error);
    } finally {
        // Re-enable send button
        sendButton.disabled = false;
    }
}

// Auto-scroll to bottom when new messages are added
const chatMessages = document.getElementById('chatMessages');
if (chatMessages) {
    const observer = new MutationObserver(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    observer.observe(chatMessages, { childList: true });
}

