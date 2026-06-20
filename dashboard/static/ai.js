/**
 * FINESE2 Dashboard - AI Chat Module
 * Handles AI chat with streaming support
 */

class AIChat {
    constructor() {
        this.messages = [];
        this.isStreaming = false;
        this._initialized = false;
        this.config = {
            provider: 'openai',
            model: 'gpt-4o-mini',
            api_key: '',
            base_url: '',
            temperature: 0.7,
            max_tokens: 4096,
            system_prompt: 'You are FINESE2 AI Assistant, a helpful data science expert. Help users with data analysis, machine learning, and statistical questions.'
        };
        this.messageContainer = null;
        this.inputElement = null;
    }

    init(containerId, inputId) {
        if (this._initialized) return;
        this._initialized = true;
        
        this.messageContainer = document.getElementById(containerId);
        this.inputElement = document.getElementById(inputId);

        if (this.inputElement) {
            this.inputElement.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        this.loadConfig();
        this.renderWelcome();
    }

    renderWelcome() {
        if (!this.messageContainer) return;
        this.messageContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🤖</div>
                <h3>FINESE2 AI Assistant</h3>
                <p>Ask me anything about data analysis, machine learning, statistics, or your current dataset.</p>
                <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;">
                    <button class="btn btn-secondary btn-sm" onclick="ai.quickQuestion('Summarize my dataset')">📊 Summarize dataset</button>
                    <button class="btn btn-secondary btn-sm" onclick="ai.quickQuestion('What cleaning steps do you recommend?')">🧹 Cleaning tips</button>
                    <button class="btn btn-secondary btn-sm" onclick="ai.quickQuestion('Suggest features for modeling')">🤖 Feature suggestions</button>
                    <button class="btn btn-secondary btn-sm" onclick="ai.quickQuestion('Explain the correlations')">📈 Explain correlations</button>
                </div>
            </div>
        `;
    }

    async loadConfig() {
        try {
            const saved = localStorage.getItem('finese2_ai_config');
            if (saved) {
                this.config = { ...this.config, ...JSON.parse(saved) };
            }
        } catch (e) {
            console.warn('Could not load AI config:', e);
        }
    }

    saveConfig() {
        localStorage.setItem('finese2_ai_config', JSON.stringify(this.config));
    }

    async configure(config) {
        this.config = { ...this.config, ...config };
        this.saveConfig();
        try {
            const result = await api.configureAI(this.config);
            showNotification('AI configuration saved', 'success');
            return result;
        } catch (error) {
            showNotification('Failed to save AI config: ' + error.message, 'error');
        }
    }

    async validate() {
        try {
            const result = await api.validateAIConfig(this.config);
            if (result.valid) {
                showNotification('AI connection successful!', 'success');
            } else {
                showNotification('AI connection failed: ' + (result.error || 'Unknown error'), 'error');
            }
            return result;
        } catch (error) {
            showNotification('Validation error: ' + error.message, 'error');
            return { valid: false, error: error.message };
        }
    }

    addMessage(role, content) {
        if (!this.messageContainer) return;

        // Remove empty state if present
        const emptyState = this.messageContainer.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${role}`;

        if (role === 'user') {
            msgDiv.textContent = content;
        } else {
            msgDiv.innerHTML = this.formatMarkdown(content);
        }

        this.messageContainer.appendChild(msgDiv);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        return msgDiv;
    }

    addStreamingMessage() {
        if (!this.messageContainer) return null;

        const emptyState = this.messageContainer.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message assistant';
        msgDiv.innerHTML = '<span class="streaming-cursor">▊</span>';
        this.messageContainer.appendChild(msgDiv);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        return msgDiv;
    }

    formatMarkdown(text) {
        // Basic markdown formatting
        return text
            .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/^### (.+)$/gm, '<h4>$1</h4>')
            .replace(/^## (.+)$/gm, '<h3>$1</h3>')
            .replace(/^# (.+)$/gm, '<h2>$1</h2>')
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            .replace(/\n/g, '<br>');
    }

    async sendMessage(text = null) {
        const message = text || (this.inputElement ? this.inputElement.value.trim() : '');
        if (!message || this.isStreaming) return;

        // Clear input
        if (this.inputElement) this.inputElement.value = '';

        // Add user message
        this.addMessage('user', message);
        this.messages.push({ role: 'user', content: message });

        // Show loading
        this.isStreaming = true;
        const streamDiv = this.addStreamingMessage();

        try {
            const response = await api.chatWithAI(message, this.messages.slice(0, -1));

            if (streamDiv) {
                streamDiv.innerHTML = this.formatMarkdown(response.response || response.content || 'No response received.');
            }

            this.messages.push({
                role: 'assistant',
                content: response.response || response.content || ''
            });
        } catch (error) {
            if (streamDiv) {
                streamDiv.innerHTML = `<span style="color: var(--danger);">Error: ${error.message}</span>`;
            }
            showNotification('AI request failed: ' + error.message, 'error');
        } finally {
            this.isStreaming = false;
        }
    }

    quickQuestion(question) {
        this.sendMessage(question);
    }

    clearHistory() {
        this.messages = [];
        this.renderWelcome();
    }
}

const ai = new AIChat();
