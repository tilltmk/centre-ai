/**
 * Centre AI Dashboard
 * Interactive JavaScript for MCP Server Dashboard
 */

// ============================================
// Theme Management
// ============================================

class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme();
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const icon = document.querySelector('.theme-icon');
        if (icon) {
            icon.textContent = this.theme === 'dark' ? '☀️' : '🌙';
        }
    }

    toggle() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.applyTheme();
    }
}

// ============================================
// API Client
// ============================================

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.apiKey = localStorage.getItem('api_key') || 'dev-api-key-12345';
    }

    setAPIKey(key) {
        this.apiKey = key;
        localStorage.setItem('api_key', key);
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey,
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    async getStatus() {
        return this.request('/api/status');
    }

    async getStats() {
        return this.request('/api/stats');
    }

    async listTools() {
        return this.request('/mcp/tools/list');
    }

    async executeTool(toolName, parameters) {
        return this.request('/mcp/tools/execute', {
            method: 'POST',
            body: JSON.stringify({
                tool_name: toolName,
                parameters: parameters
            })
        });
    }
}

// ============================================
// Dashboard Controller
// ============================================

class Dashboard {
    constructor() {
        this.api = new APIClient();
        this.tools = [];
        this.init();
    }

    async init() {
        // Load API key from input if exists
        const apiKeyInput = document.getElementById('api-key-input');
        if (apiKeyInput) {
            apiKeyInput.value = this.api.apiKey;
            apiKeyInput.addEventListener('change', (e) => {
                this.api.setAPIKey(e.target.value);
                this.loadData();
            });
        }

        // Setup event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadData();

        // Auto-refresh every 30 seconds
        setInterval(() => this.loadData(), 30000);
    }

    setupEventListeners() {
        // Refresh tools button
        const refreshBtn = document.getElementById('refresh-tools');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadTools());
        }

        // Execute tool button
        const executeBtn = document.getElementById('execute-tool');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => this.executeTool());
        }
    }

    async loadData() {
        await Promise.all([
            this.loadStatus(),
            this.loadStats(),
            this.loadTools()
        ]);
    }

    async loadStatus() {
        try {
            const data = await this.api.getStatus();

            // Update status
            const statusText = document.getElementById('server-status');
            if (statusText) {
                statusText.textContent = data.status === 'running' ? 'Online' : 'Offline';
            }

            // Update version
            const versionText = document.getElementById('server-version');
            if (versionText) {
                versionText.textContent = data.version || '-';
            }

            // Update initialized status
            const initializedText = document.getElementById('server-initialized');
            if (initializedText) {
                initializedText.textContent = data.mcp_server?.initialized ? 'Ja' : 'Nein';
            }

            // Update tools count
            const toolsCount = document.getElementById('tools-count');
            if (toolsCount) {
                toolsCount.textContent = data.mcp_server?.tools_count || 0;
            }

            // Update memory count
            const memoryCount = document.getElementById('memory-count');
            if (memoryCount) {
                memoryCount.textContent = data.mcp_server?.memory_items || 0;
            }

        } catch (error) {
            console.error('Failed to load status:', error);
            this.showError('Status konnte nicht geladen werden');
        }
    }

    async loadStats() {
        try {
            const data = await this.api.getStats();

            // Update requests count
            const requestsCount = document.getElementById('requests-count');
            if (requestsCount) {
                requestsCount.textContent = data.total_requests || 0;
            }

        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async loadTools() {
        try {
            const data = await this.api.listTools();
            this.tools = data.tools || [];

            // Render tools grid
            this.renderTools();

            // Update tools dropdown
            this.updateToolsDropdown();

        } catch (error) {
            console.error('Failed to load tools:', error);
            this.showError('Tools konnten nicht geladen werden');
        }
    }

    renderTools() {
        const toolsList = document.getElementById('tools-list');
        if (!toolsList) return;

        if (this.tools.length === 0) {
            toolsList.innerHTML = '<p style="color: var(--text-secondary);">Keine Tools verfügbar</p>';
            return;
        }

        toolsList.innerHTML = this.tools.map(tool => `
            <div class="tool-item">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description || 'Keine Beschreibung'}</div>
            </div>
        `).join('');
    }

    updateToolsDropdown() {
        const toolSelect = document.getElementById('tool-select');
        if (!toolSelect) return;

        toolSelect.innerHTML = '<option value="">-- Tool wählen --</option>' +
            this.tools.map(tool => `
                <option value="${tool.name}">${tool.name}</option>
            `).join('');
    }

    async executeTool() {
        const toolSelect = document.getElementById('tool-select');
        const paramsInput = document.getElementById('params-input');
        const resultDiv = document.getElementById('api-result');
        const resultContent = document.getElementById('api-result-content');

        if (!toolSelect || !paramsInput || !resultDiv || !resultContent) return;

        const toolName = toolSelect.value;
        if (!toolName) {
            alert('Bitte wähle ein Tool aus');
            return;
        }

        let parameters = {};
        try {
            if (paramsInput.value.trim()) {
                parameters = JSON.parse(paramsInput.value);
            }
        } catch (error) {
            alert('Ungültiges JSON in den Parametern');
            return;
        }

        try {
            // Show loading
            resultDiv.style.display = 'block';
            resultContent.textContent = 'Wird ausgeführt...';

            // Execute tool
            const result = await this.api.executeTool(toolName, parameters);

            // Show result
            resultContent.textContent = JSON.stringify(result, null, 2);

            // Refresh stats
            await this.loadStats();

        } catch (error) {
            resultContent.textContent = `Fehler: ${error.message}`;
        }
    }

    showError(message) {
        console.error(message);
        // Could implement a toast notification here
    }
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    new ThemeManager();

    // Initialize dashboard
    new Dashboard();

    console.log('Centre AI Dashboard initialized');
});
