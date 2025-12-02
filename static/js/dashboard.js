/**
 * Centre AI Dashboard
 * Complete Knowledge Management System
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
            icon.textContent = this.theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
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

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Status & Stats
    async getStatus() { return this.request('/api/status'); }
    async getStats() { return this.request('/api/stats'); }
    async listTools() { return this.request('/mcp/tools/list'); }

    async executeTool(toolName, parameters) {
        return this.request('/mcp/tools/execute', {
            method: 'POST',
            body: JSON.stringify({ tool_name: toolName, parameters })
        });
    }

    // Git Repositories
    async listRepos() { return this.request('/api/git/repos'); }

    async cloneRepo(data) {
        return this.request('/api/git/clone', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteRepo(repoName) {
        return this.request(`/api/git/repos/${encodeURIComponent(repoName)}`, { method: 'DELETE' });
    }

    async pullRepo(repoName) {
        return this.request(`/api/git/repos/${encodeURIComponent(repoName)}/pull`, { method: 'POST' });
    }

    async indexRepo(repoName) {
        return this.request(`/api/git/repos/${encodeURIComponent(repoName)}/index`, { method: 'POST' });
    }

    // Memories
    async listMemories(params = {}) {
        const query = new URLSearchParams();
        if (params.memory_type) query.set('memory_type', params.memory_type);
        if (params.query) query.set('query', params.query);
        return this.request(`/api/memories?${query}`);
    }

    async createMemory(data) {
        return this.request('/api/memories', { method: 'POST', body: JSON.stringify(data) });
    }

    async deleteMemory(id) {
        return this.request(`/api/memories/${id}`, { method: 'DELETE' });
    }

    // Artifacts
    async listArtifacts(params = {}) {
        const query = new URLSearchParams();
        if (params.type) query.set('type', params.type);
        if (params.query) query.set('query', params.query);
        return this.request(`/api/artifacts?${query}`);
    }

    async createArtifact(data) {
        return this.request('/api/artifacts', { method: 'POST', body: JSON.stringify(data) });
    }

    async getArtifact(id) {
        return this.request(`/api/artifacts/${id}`);
    }

    async deleteArtifact(id) {
        return this.request(`/api/artifacts/${id}`, { method: 'DELETE' });
    }

    // Instructions
    async listInstructions(params = {}) {
        const query = new URLSearchParams();
        if (params.scope) query.set('scope', params.scope);
        return this.request(`/api/instructions?${query}`);
    }

    async createInstruction(data) {
        return this.request('/api/instructions', { method: 'POST', body: JSON.stringify(data) });
    }

    async deleteInstruction(id) {
        return this.request(`/api/instructions/${id}`, { method: 'DELETE' });
    }

    // Projects
    async listProjects(params = {}) {
        const query = new URLSearchParams();
        if (params.status) query.set('status', params.status);
        return this.request(`/api/projects?${query}`);
    }

    async createProject(data) {
        return this.request('/api/projects', { method: 'POST', body: JSON.stringify(data) });
    }

    async getProject(id) {
        return this.request(`/api/projects/${id}`);
    }

    async deleteProject(id) {
        return this.request(`/api/projects/${id}`, { method: 'DELETE' });
    }

    // Knowledge Graph
    async getGraph(params = {}) {
        const query = new URLSearchParams();
        if (params.node_type) query.set('node_type', params.node_type);
        if (params.limit) query.set('limit', params.limit);
        return this.request(`/api/knowledge/graph?${query}`);
    }

    async listKnowledgeNodes(params = {}) {
        const query = new URLSearchParams();
        if (params.node_type) query.set('node_type', params.node_type);
        if (params.query) query.set('query', params.query);
        return this.request(`/api/knowledge/nodes?${query}`);
    }

    async createKnowledgeNode(data) {
        return this.request('/api/knowledge/nodes', { method: 'POST', body: JSON.stringify(data) });
    }

    async deleteKnowledgeNode(id) {
        return this.request(`/api/knowledge/nodes/${id}`, { method: 'DELETE' });
    }

    async createConnection(data) {
        return this.request('/api/knowledge/connect', { method: 'POST', body: JSON.stringify(data) });
    }

    async connectEntities(data) {
        return this.request('/api/knowledge/connect-entities', { method: 'POST', body: JSON.stringify(data) });
    }

    async getNodeConnections(nodeId) {
        return this.request(`/api/knowledge/nodes/${nodeId}/connections`);
    }
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================
// Debounce Utility
// ============================================

let debounceTimer;
function debounce(func, delay) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(func, delay);
}

// ============================================
// Tab Navigation
// ============================================

function switchTab(tabName) {
    // Update nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });

    // Load data for the tab
    switch(tabName) {
        case 'repositories': loadRepositories(); break;
        case 'memories': loadMemories(); break;
        case 'artifacts': loadArtifacts(); break;
        case 'instructions': loadInstructions(); break;
        case 'projects': loadProjects(); break;
        case 'knowledge': loadKnowledgeGraph(); break;
        case 'tools': loadTools(); break;
        case 'tasks': loadTasks(); loadProjectsForSelect(); break;
        case 'notes': loadNotes(); break;
        case 'triggers': loadTriggers(); break;
        case 'conversations': loadConversations(); break;
    }
}

// ============================================
// Dashboard Controller
// ============================================

const api = new APIClient();
let tools = [];

async function loadDashboard() {
    try {
        const [status, stats] = await Promise.all([
            api.getStatus(),
            api.getStats()
        ]);

        // Update status
        document.getElementById('server-status').textContent = status.status === 'running' ? 'Online' : 'Offline';
        document.getElementById('server-version').textContent = status.version || '-';
        document.getElementById('server-initialized').textContent = status.mcp_server?.initialized ? 'Ja' : 'Nein';
        document.getElementById('tools-count').textContent = status.mcp_server?.tools_count || 0;
        document.getElementById('memory-count').textContent = status.mcp_server?.memory_items || 0;
        document.getElementById('requests-count').textContent = stats.total_requests || 0;

    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// ============================================
// Repositories
// ============================================

async function loadRepositories() {
    const container = document.getElementById('repos-list');
    container.innerHTML = '<div class="loading-state">Repositories werden geladen...</div>';

    try {
        const data = await api.listRepos();
        const repos = data.repos || [];

        if (repos.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128193;</div>
                    <p>Keine Repositories vorhanden</p>
                    <button class="btn btn-primary" onclick="showCloneModal()">Repository klonen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = repos.map(repo => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${repo.name}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${repo.branch}</span>
                            <span class="list-item-badge">${repo.commit}</span>
                            ${repo.is_dirty ? '<span class="list-item-badge warning">Uncommitted changes</span>' : ''}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-secondary btn-small" onclick="pullRepository('${repo.name}')">Pull</button>
                        <button class="btn btn-secondary btn-small" onclick="indexRepository('${repo.name}')">Index</button>
                        <button class="btn btn-danger btn-small" onclick="deleteRepository('${repo.name}')">Delete</button>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showCloneModal() {
    document.getElementById('clone-modal').style.display = 'flex';
}

function hideCloneModal() {
    document.getElementById('clone-modal').style.display = 'none';
    document.getElementById('repo-url').value = '';
    document.getElementById('repo-branch').value = 'main';
    document.getElementById('repo-username').value = '';
    document.getElementById('repo-password').value = '';
    document.getElementById('repo-depth').value = '';
}

async function cloneRepository() {
    const url = document.getElementById('repo-url').value.trim();
    const branch = document.getElementById('repo-branch').value.trim() || 'main';
    const username = document.getElementById('repo-username').value.trim();
    const password = document.getElementById('repo-password').value.trim();
    const depth = document.getElementById('repo-depth').value;

    if (!url) {
        showToast('Bitte Repository URL eingeben', 'error');
        return;
    }

    try {
        const data = { repo_url: url, branch };
        if (username) data.username = username;
        if (password) data.password = password;
        if (depth) data.depth = parseInt(depth);

        const result = await api.cloneRepo(data);

        if (result.success) {
            showToast(`Repository ${result.repo_name} erfolgreich geklont`);
            hideCloneModal();
            loadRepositories();
        } else {
            showToast(result.error || 'Fehler beim Klonen', 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function pullRepository(name) {
    try {
        const result = await api.pullRepo(name);
        if (result.success) {
            showToast(`${name} aktualisiert`);
            loadRepositories();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function indexRepository(name) {
    showToast(`Indexiere ${name}...`, 'warning');
    try {
        const result = await api.indexRepo(name);
        if (result.success) {
            showToast(`${result.indexed_files} Dateien indexiert`);
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteRepository(name) {
    if (!confirm(`Repository "${name}" wirklich loeschen?`)) return;

    try {
        const result = await api.deleteRepo(name);
        if (result.success) {
            showToast(`${name} geloescht`);
            loadRepositories();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Memories
// ============================================

async function loadMemories() {
    const container = document.getElementById('memories-list');
    container.innerHTML = '<div class="loading-state">Memories werden geladen...</div>';

    const typeFilter = document.getElementById('memory-type-filter')?.value;
    const searchQuery = document.getElementById('memory-search')?.value;

    try {
        const data = await api.listMemories({ memory_type: typeFilter, query: searchQuery });
        const memories = data.memories || [];

        if (memories.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128161;</div>
                    <p>Keine Memories vorhanden</p>
                    <button class="btn btn-primary" onclick="showMemoryModal()">Memory erstellen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = memories.map(mem => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${mem.memory_type}</span>
                            <span class="list-item-badge">Wichtigkeit: ${mem.importance}</span>
                            ${(mem.tags || []).map(t => `<span class="list-item-badge">${t}</span>`).join('')}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-danger btn-small" onclick="deleteMemory(${mem.id})">Delete</button>
                    </div>
                </div>
                <div class="list-item-content">${escapeHtml(mem.content)}</div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showMemoryModal() {
    document.getElementById('memory-modal').style.display = 'flex';
}

function hideMemoryModal() {
    document.getElementById('memory-modal').style.display = 'none';
    document.getElementById('memory-content').value = '';
    document.getElementById('memory-type').value = 'fact';
    document.getElementById('memory-importance').value = '5';
    document.getElementById('memory-tags').value = '';
}

async function saveMemory() {
    const content = document.getElementById('memory-content').value.trim();
    const memory_type = document.getElementById('memory-type').value;
    const importance = parseInt(document.getElementById('memory-importance').value);
    const tagsStr = document.getElementById('memory-tags').value;
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

    if (!content) {
        showToast('Bitte Inhalt eingeben', 'error');
        return;
    }

    try {
        const result = await api.createMemory({ content, memory_type, importance, tags });
        if (result.success) {
            showToast('Memory gespeichert');
            hideMemoryModal();
            loadMemories();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteMemory(id) {
    if (!confirm('Memory wirklich loeschen?')) return;

    try {
        const result = await api.deleteMemory(id);
        if (result.success) {
            showToast('Memory geloescht');
            loadMemories();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Artifacts
// ============================================

async function loadArtifacts() {
    const container = document.getElementById('artifacts-list');
    container.innerHTML = '<div class="loading-state">Artifacts werden geladen...</div>';

    const typeFilter = document.getElementById('artifact-type-filter')?.value;
    const searchQuery = document.getElementById('artifact-search')?.value;

    try {
        const data = await api.listArtifacts({ type: typeFilter, query: searchQuery });
        const artifacts = data.artifacts || [];

        if (artifacts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128196;</div>
                    <p>Keine Artifacts vorhanden</p>
                    <button class="btn btn-primary" onclick="showArtifactModal()">Artifact erstellen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = artifacts.map(art => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(art.title)}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${art.artifact_type}</span>
                            ${art.language ? `<span class="list-item-badge">${art.language}</span>` : ''}
                            <span class="list-item-badge">v${art.version}</span>
                            ${(art.tags || []).map(t => `<span class="list-item-badge">${t}</span>`).join('')}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-secondary btn-small" onclick="viewArtifact(${art.id})">View</button>
                        <button class="btn btn-danger btn-small" onclick="deleteArtifact(${art.id})">Delete</button>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showArtifactModal() {
    document.getElementById('artifact-modal').style.display = 'flex';
    updateArtifactLanguage();
}

function hideArtifactModal() {
    document.getElementById('artifact-modal').style.display = 'none';
    document.getElementById('artifact-title').value = '';
    document.getElementById('artifact-content').value = '';
    document.getElementById('artifact-type').value = 'code';
    document.getElementById('artifact-tags').value = '';
}

function updateArtifactLanguage() {
    const type = document.getElementById('artifact-type').value;
    const langGroup = document.getElementById('language-group');
    langGroup.style.display = type === 'code' ? 'block' : 'none';
}

async function saveArtifact() {
    const title = document.getElementById('artifact-title').value.trim();
    const content = document.getElementById('artifact-content').value;
    const artifact_type = document.getElementById('artifact-type').value;
    const language = artifact_type === 'code' ? document.getElementById('artifact-language').value : null;
    const tagsStr = document.getElementById('artifact-tags').value;
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

    if (!title || !content) {
        showToast('Bitte Titel und Inhalt eingeben', 'error');
        return;
    }

    try {
        const data = { title, content, artifact_type, tags };
        if (language) data.language = language;

        const result = await api.createArtifact(data);
        if (result.success) {
            showToast('Artifact gespeichert');
            hideArtifactModal();
            loadArtifacts();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function viewArtifact(id) {
    try {
        const data = await api.getArtifact(id);
        if (data.success && data.artifact) {
            const art = data.artifact;
            alert(`Titel: ${art.title}\n\nTyp: ${art.artifact_type}\n\nInhalt:\n${art.content.substring(0, 500)}${art.content.length > 500 ? '...' : ''}`);
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteArtifact(id) {
    if (!confirm('Artifact wirklich loeschen?')) return;

    try {
        const result = await api.deleteArtifact(id);
        if (result.success) {
            showToast('Artifact geloescht');
            loadArtifacts();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Instructions
// ============================================

async function loadInstructions() {
    const container = document.getElementById('instructions-list');
    container.innerHTML = '<div class="loading-state">Instructions werden geladen...</div>';

    const scopeFilter = document.getElementById('instruction-scope-filter')?.value;

    try {
        const data = await api.listInstructions({ scope: scopeFilter });
        const instructions = data.instructions || [];

        if (instructions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128221;</div>
                    <p>Keine Instructions vorhanden</p>
                    <button class="btn btn-primary" onclick="showInstructionModal()">Instruction erstellen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = instructions.map(inst => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(inst.title)}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${inst.scope}</span>
                            ${inst.category ? `<span class="list-item-badge">${inst.category}</span>` : ''}
                            <span class="list-item-badge">Prioritaet: ${inst.priority}</span>
                            ${inst.is_active ? '<span class="list-item-badge success">Aktiv</span>' : '<span class="list-item-badge">Inaktiv</span>'}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-danger btn-small" onclick="deleteInstruction(${inst.id})">Delete</button>
                    </div>
                </div>
                <div class="list-item-content">${escapeHtml(inst.content)}</div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showInstructionModal() {
    document.getElementById('instruction-modal').style.display = 'flex';
}

function hideInstructionModal() {
    document.getElementById('instruction-modal').style.display = 'none';
    document.getElementById('instruction-title').value = '';
    document.getElementById('instruction-content').value = '';
    document.getElementById('instruction-category').value = '';
    document.getElementById('instruction-scope').value = 'global';
    document.getElementById('instruction-priority').value = '5';
}

async function saveInstruction() {
    const title = document.getElementById('instruction-title').value.trim();
    const content = document.getElementById('instruction-content').value.trim();
    const category = document.getElementById('instruction-category').value.trim();
    const scope = document.getElementById('instruction-scope').value;
    const priority = parseInt(document.getElementById('instruction-priority').value);

    if (!title || !content) {
        showToast('Bitte Titel und Inhalt eingeben', 'error');
        return;
    }

    try {
        const data = { title, content, scope, priority };
        if (category) data.category = category;

        const result = await api.createInstruction(data);
        if (result.success) {
            showToast('Instruction gespeichert');
            hideInstructionModal();
            loadInstructions();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteInstruction(id) {
    if (!confirm('Instruction wirklich loeschen?')) return;

    try {
        const result = await api.deleteInstruction(id);
        if (result.success) {
            showToast('Instruction geloescht');
            loadInstructions();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Projects
// ============================================

async function loadProjects() {
    const container = document.getElementById('projects-list');
    container.innerHTML = '<div class="loading-state">Projekte werden geladen...</div>';

    const statusFilter = document.getElementById('project-status-filter')?.value;

    try {
        const data = await api.listProjects({ status: statusFilter });
        const projects = data.projects || [];

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128194;</div>
                    <p>Keine Projekte vorhanden</p>
                    <button class="btn btn-primary" onclick="showProjectModal()">Projekt erstellen</button>
                </div>
            `;
            return;
        }

        const statusColors = {
            'active': 'success',
            'paused': 'warning',
            'completed': 'primary',
            'archived': ''
        };

        container.innerHTML = projects.map(proj => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(proj.name)}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge ${statusColors[proj.status] || ''}">${proj.status}</span>
                            <span class="list-item-badge">Prioritaet: ${proj.priority}</span>
                            ${(proj.tags || []).map(t => `<span class="list-item-badge">${t}</span>`).join('')}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-secondary btn-small" onclick="viewProject(${proj.id})">View</button>
                        <button class="btn btn-danger btn-small" onclick="deleteProject(${proj.id})">Delete</button>
                    </div>
                </div>
                ${proj.description ? `<div class="list-item-content">${escapeHtml(proj.description)}</div>` : ''}
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showProjectModal() {
    document.getElementById('project-modal').style.display = 'flex';
}

function hideProjectModal() {
    document.getElementById('project-modal').style.display = 'none';
    document.getElementById('project-name').value = '';
    document.getElementById('project-description').value = '';
    document.getElementById('project-priority').value = '5';
    document.getElementById('project-tags').value = '';
}

async function saveProject() {
    const name = document.getElementById('project-name').value.trim();
    const description = document.getElementById('project-description').value.trim();
    const priority = parseInt(document.getElementById('project-priority').value);
    const tagsStr = document.getElementById('project-tags').value;
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

    if (!name) {
        showToast('Bitte Projekt-Name eingeben', 'error');
        return;
    }

    try {
        const data = { name, priority, tags };
        if (description) data.description = description;

        const result = await api.createProject(data);
        if (result.success) {
            showToast('Projekt erstellt');
            hideProjectModal();
            loadProjects();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function viewProject(id) {
    try {
        const data = await api.getProject(id);
        if (data.success && data.project) {
            const proj = data.project;
            alert(`Projekt: ${proj.name}\n\nStatus: ${proj.status}\nPrioritaet: ${proj.priority}\n\nBeschreibung:\n${proj.description || '-'}\n\nArtefakte: ${data.artifact_count || 0}`);
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteProject(id) {
    if (!confirm('Projekt wirklich loeschen?')) return;

    try {
        const result = await api.deleteProject(id);
        if (result.success) {
            showToast('Projekt geloescht');
            loadProjects();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Knowledge Graph
// ============================================

let graphData = { nodes: [], edges: [] };
let graphCanvas = null;
let graphCtx = null;
let graphNodes = [];
let selectedNode = null;
let isDragging = false;
let dragNode = null;
let offsetX = 0;
let offsetY = 0;

const nodeColors = {
    'concept': '#0a84ff',
    'entity': '#30d158',
    'topic': '#ff9f0a',
    'reference': '#bf5af2',
    'memory_ref': '#64d2ff',
    'artifact_ref': '#ff6482',
    'project_ref': '#ffd60a',
    'instruction_ref': '#ac8e68',
    'idea': '#5e5ce6',
    'question': '#ff453a'
};

async function loadKnowledgeGraph() {
    const container = document.getElementById('knowledge-nodes-list');
    container.innerHTML = '<div class="loading-state">Graph wird geladen...</div>';

    try {
        const [graphResult, nodesResult] = await Promise.all([
            api.getGraph({ limit: 100 }),
            api.listKnowledgeNodes({})
        ]);

        if (graphResult.success) {
            graphData = graphResult.graph || { nodes: [], edges: [] };
            initGraphCanvas();
            renderGraph();
        }

        if (nodesResult.success) {
            renderNodesList(nodesResult.nodes || []);
            populateNodeSelects(nodesResult.nodes || []);
        }

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function initGraphCanvas() {
    graphCanvas = document.getElementById('knowledge-graph-canvas');
    if (!graphCanvas) return;

    const wrapper = graphCanvas.parentElement;
    graphCanvas.width = wrapper.clientWidth;
    graphCanvas.height = 400;
    graphCtx = graphCanvas.getContext('2d');

    // Initialize node positions
    graphNodes = graphData.nodes.map((node, i) => ({
        ...node,
        x: 100 + (i % 5) * 150 + Math.random() * 50,
        y: 80 + Math.floor(i / 5) * 100 + Math.random() * 30,
        vx: 0,
        vy: 0,
        radius: 25
    }));

    // Add mouse events
    graphCanvas.addEventListener('mousedown', onGraphMouseDown);
    graphCanvas.addEventListener('mousemove', onGraphMouseMove);
    graphCanvas.addEventListener('mouseup', onGraphMouseUp);
    graphCanvas.addEventListener('mouseleave', onGraphMouseUp);

    // Apply force simulation
    applyForceSimulation();
}

function applyForceSimulation() {
    const iterations = 50;

    for (let iter = 0; iter < iterations; iter++) {
        // Repulsion between nodes
        for (let i = 0; i < graphNodes.length; i++) {
            for (let j = i + 1; j < graphNodes.length; j++) {
                const dx = graphNodes[j].x - graphNodes[i].x;
                const dy = graphNodes[j].y - graphNodes[i].y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = 5000 / (dist * dist);

                graphNodes[i].vx -= (dx / dist) * force;
                graphNodes[i].vy -= (dy / dist) * force;
                graphNodes[j].vx += (dx / dist) * force;
                graphNodes[j].vy += (dy / dist) * force;
            }
        }

        // Attraction along edges
        for (const edge of graphData.edges) {
            const source = graphNodes.find(n => n.id === edge.source_id);
            const target = graphNodes.find(n => n.id === edge.target_id);
            if (source && target) {
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = dist * 0.01;

                source.vx += (dx / dist) * force;
                source.vy += (dy / dist) * force;
                target.vx -= (dx / dist) * force;
                target.vy -= (dy / dist) * force;
            }
        }

        // Apply velocities and damping
        for (const node of graphNodes) {
            node.x += node.vx * 0.1;
            node.y += node.vy * 0.1;
            node.vx *= 0.9;
            node.vy *= 0.9;

            // Keep within bounds
            node.x = Math.max(40, Math.min(graphCanvas.width - 40, node.x));
            node.y = Math.max(40, Math.min(graphCanvas.height - 40, node.y));
        }
    }
}

function renderGraph() {
    if (!graphCtx) return;

    graphCtx.clearRect(0, 0, graphCanvas.width, graphCanvas.height);

    // Draw edges
    graphCtx.strokeStyle = getComputedStyle(document.documentElement)
        .getPropertyValue('--border-color').trim() || '#e5e5e7';
    graphCtx.lineWidth = 1.5;

    for (const edge of graphData.edges) {
        const source = graphNodes.find(n => n.id === edge.source_id);
        const target = graphNodes.find(n => n.id === edge.target_id);
        if (source && target) {
            graphCtx.beginPath();
            graphCtx.moveTo(source.x, source.y);
            graphCtx.lineTo(target.x, target.y);
            graphCtx.stroke();

            // Draw relationship label
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            graphCtx.fillStyle = getComputedStyle(document.documentElement)
                .getPropertyValue('--text-secondary').trim() || '#86868b';
            graphCtx.font = '10px -apple-system, sans-serif';
            graphCtx.textAlign = 'center';
            graphCtx.fillText(edge.relationship || '', midX, midY - 5);
        }
    }

    // Draw nodes
    for (const node of graphNodes) {
        const color = nodeColors[node.node_type] || '#0a84ff';

        // Node circle
        graphCtx.beginPath();
        graphCtx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        graphCtx.fillStyle = color;
        graphCtx.fill();

        // Highlight if selected
        if (selectedNode && selectedNode.id === node.id) {
            graphCtx.strokeStyle = '#ffffff';
            graphCtx.lineWidth = 3;
            graphCtx.stroke();
        }

        // Node label
        graphCtx.fillStyle = '#ffffff';
        graphCtx.font = 'bold 11px -apple-system, sans-serif';
        graphCtx.textAlign = 'center';
        graphCtx.textBaseline = 'middle';
        const label = (node.title || '').substring(0, 8);
        graphCtx.fillText(label, node.x, node.y);
    }
}

function onGraphMouseDown(e) {
    const rect = graphCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    for (const node of graphNodes) {
        const dx = x - node.x;
        const dy = y - node.y;
        if (dx * dx + dy * dy < node.radius * node.radius) {
            isDragging = true;
            dragNode = node;
            offsetX = dx;
            offsetY = dy;
            selectedNode = node;
            showNodeTooltip(node, e.clientX, e.clientY);
            break;
        }
    }
    renderGraph();
}

function onGraphMouseMove(e) {
    const rect = graphCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (isDragging && dragNode) {
        dragNode.x = x - offsetX;
        dragNode.y = y - offsetY;
        renderGraph();
    } else {
        // Check hover
        let hovered = null;
        for (const node of graphNodes) {
            const dx = x - node.x;
            const dy = y - node.y;
            if (dx * dx + dy * dy < node.radius * node.radius) {
                hovered = node;
                break;
            }
        }
        if (hovered) {
            graphCanvas.style.cursor = 'pointer';
            showNodeTooltip(hovered, e.clientX, e.clientY);
        } else {
            graphCanvas.style.cursor = 'default';
            hideNodeTooltip();
        }
    }
}

function onGraphMouseUp() {
    isDragging = false;
    dragNode = null;
}

function showNodeTooltip(node, x, y) {
    const tooltip = document.getElementById('graph-tooltip');
    if (!tooltip) return;

    tooltip.innerHTML = `
        <strong>${escapeHtml(node.title)}</strong><br>
        <span class="tooltip-type">${node.node_type}</span>
        ${node.content ? `<p>${escapeHtml(node.content.substring(0, 100))}...</p>` : ''}
    `;
    tooltip.style.display = 'block';
    tooltip.style.left = (x + 10) + 'px';
    tooltip.style.top = (y + 10) + 'px';
}

function hideNodeTooltip() {
    const tooltip = document.getElementById('graph-tooltip');
    if (tooltip) tooltip.style.display = 'none';
}

function renderNodesList(nodes) {
    const container = document.getElementById('knowledge-nodes-list');

    if (nodes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">&#128279;</div>
                <p>Keine Nodes vorhanden</p>
                <button class="btn btn-primary" onclick="showNodeModal()">Node erstellen</button>
            </div>
        `;
        return;
    }

    container.innerHTML = nodes.map(node => `
        <div class="list-item">
            <div class="list-item-header">
                <div>
                    <div class="list-item-title">${escapeHtml(node.title)}</div>
                    <div class="list-item-meta">
                        <span class="list-item-badge" style="background: ${nodeColors[node.node_type] || '#0a84ff'}; color: white;">
                            ${node.node_type}
                        </span>
                        <span class="list-item-badge">ID: ${node.id}</span>
                    </div>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-secondary btn-small" onclick="showNodeConnections(${node.id})">Verbindungen</button>
                    <button class="btn btn-danger btn-small" onclick="deleteNode(${node.id})">Delete</button>
                </div>
            </div>
            ${node.content ? `<div class="list-item-content">${escapeHtml(node.content)}</div>` : ''}
        </div>
    `).join('');
}

function populateNodeSelects(nodes) {
    const sourceSelect = document.getElementById('connection-source');
    const targetSelect = document.getElementById('connection-target');

    if (!sourceSelect || !targetSelect) return;

    const options = '<option value="">-- Node auswaehlen --</option>' +
        nodes.map(n => `<option value="${n.id}">${n.title} (${n.node_type})</option>`).join('');

    sourceSelect.innerHTML = options;
    targetSelect.innerHTML = options;
}

function filterGraph() {
    const typeFilter = document.getElementById('graph-filter-type')?.value;
    loadKnowledgeGraph();
}

function searchNodes() {
    const query = document.getElementById('graph-search')?.value;
    if (query && query.length > 1) {
        api.listKnowledgeNodes({ query }).then(result => {
            if (result.success) {
                renderNodesList(result.nodes || []);
            }
        });
    } else {
        loadKnowledgeGraph();
    }
}

// Node Modal
function showNodeModal() {
    document.getElementById('node-modal').style.display = 'flex';
}

function hideNodeModal() {
    document.getElementById('node-modal').style.display = 'none';
    document.getElementById('node-title').value = '';
    document.getElementById('node-type').value = 'concept';
    document.getElementById('node-content').value = '';
}

async function saveNode() {
    const title = document.getElementById('node-title').value.trim();
    const node_type = document.getElementById('node-type').value;
    const content = document.getElementById('node-content').value.trim();

    if (!title) {
        showToast('Bitte Titel eingeben', 'error');
        return;
    }

    try {
        const data = { title, node_type };
        if (content) data.content = content;

        const result = await api.createKnowledgeNode(data);
        if (result.success) {
            showToast('Node erstellt');
            hideNodeModal();
            loadKnowledgeGraph();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteNode(id) {
    if (!confirm('Node wirklich loeschen? Alle Verbindungen werden auch geloescht.')) return;

    try {
        const result = await api.deleteKnowledgeNode(id);
        if (result.success) {
            showToast('Node geloescht');
            loadKnowledgeGraph();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function showNodeConnections(nodeId) {
    try {
        const result = await api.getNodeConnections(nodeId);
        if (result.success) {
            const conns = result.connections || [];
            const node = result.node;
            let msg = `Verbindungen von "${node?.title}":\n\n`;
            if (conns.length === 0) {
                msg += 'Keine Verbindungen';
            } else {
                for (const c of conns) {
                    msg += `- ${c.relationship} -> ${c.connected_node?.title || 'Unknown'}\n`;
                }
            }
            alert(msg);
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Connection Modal
function showConnectionModal() {
    loadKnowledgeGraph(); // Ensure nodes are loaded for selects
    document.getElementById('connection-modal').style.display = 'flex';
}

function hideConnectionModal() {
    document.getElementById('connection-modal').style.display = 'none';
    document.getElementById('connection-source').value = '';
    document.getElementById('connection-target').value = '';
    document.getElementById('connection-relationship').value = '';
}

async function saveConnection() {
    const source_id = parseInt(document.getElementById('connection-source').value);
    const target_id = parseInt(document.getElementById('connection-target').value);
    const relationship = document.getElementById('connection-relationship').value.trim();
    const bidirectional = document.getElementById('connection-bidirectional').checked;

    if (!source_id || !target_id || !relationship) {
        showToast('Bitte alle Felder ausfuellen', 'error');
        return;
    }

    try {
        const result = await api.createConnection({ source_id, target_id, relationship, bidirectional });
        if (result.success) {
            showToast('Verbindung erstellt');
            hideConnectionModal();
            loadKnowledgeGraph();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Entity Connection Modal
function showEntityConnectionModal() {
    document.getElementById('entity-connection-modal').style.display = 'flex';
}

function hideEntityConnectionModal() {
    document.getElementById('entity-connection-modal').style.display = 'none';
}

async function connectEntities() {
    const source_type = document.getElementById('entity-source-type').value;
    const source_id = parseInt(document.getElementById('entity-source-id').value);
    const target_type = document.getElementById('entity-target-type').value;
    const target_id = parseInt(document.getElementById('entity-target-id').value);
    const relationship = document.getElementById('entity-relationship').value.trim();

    if (!source_id || !target_id || !relationship) {
        showToast('Bitte alle Felder ausfuellen', 'error');
        return;
    }

    try {
        const result = await api.connectEntities({
            source_type, source_id,
            target_type, target_id,
            relationship
        });
        if (result.success) {
            showToast('Entitaeten verbunden');
            hideEntityConnectionModal();
            loadKnowledgeGraph();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Tools
// ============================================

async function loadTools() {
    const container = document.getElementById('tools-list');
    container.innerHTML = '<div class="loading-state">Tools werden geladen...</div>';

    try {
        const data = await api.listTools();
        tools = data.tools || [];

        if (tools.length === 0) {
            container.innerHTML = '<div class="empty-state">Keine Tools verfuegbar</div>';
            return;
        }

        container.innerHTML = tools.map(tool => `
            <div class="tool-item">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description || 'Keine Beschreibung'}</div>
            </div>
        `).join('');

        // Update dropdown
        const select = document.getElementById('tool-select');
        if (select) {
            select.innerHTML = '<option value="">-- Tool wahlen --</option>' +
                tools.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
        }

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

async function executeTool() {
    const toolName = document.getElementById('tool-select').value;
    const paramsStr = document.getElementById('params-input').value;
    const resultDiv = document.getElementById('api-result');
    const resultContent = document.getElementById('api-result-content');

    if (!toolName) {
        showToast('Bitte Tool auswaehlen', 'error');
        return;
    }

    let params = {};
    try {
        if (paramsStr.trim()) {
            params = JSON.parse(paramsStr);
        }
    } catch (e) {
        showToast('Ungueltiges JSON', 'error');
        return;
    }

    resultDiv.style.display = 'block';
    resultContent.textContent = 'Wird ausgefuehrt...';

    try {
        const result = await api.executeTool(toolName, params);
        resultContent.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        resultContent.textContent = `Fehler: ${error.message}`;
    }
}

// ============================================
// Tasks
// ============================================

async function loadTasks() {
    const container = document.getElementById('tasks-list');
    container.innerHTML = '<div class="loading-state">Tasks werden geladen...</div>';

    const projectFilter = document.getElementById('task-project-filter')?.value;
    const statusFilter = document.getElementById('task-status-filter')?.value;

    try {
        const params = {};
        if (projectFilter) params.project_id = projectFilter;
        if (statusFilter) params.status = statusFilter;

        const query = new URLSearchParams(params);
        const data = await api.request(`/api/tasks?${query}`);
        const tasks = data.tasks || [];

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#9744;</div>
                    <p>Keine Tasks vorhanden</p>
                    <button class="btn btn-primary" onclick="showTaskModal()">Task erstellen</button>
                </div>
            `;
            return;
        }

        const statusColors = { pending: '', in_progress: 'warning', completed: 'success', cancelled: '' };

        container.innerHTML = tasks.map(task => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(task.title)}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge ${statusColors[task.status] || ''}">${task.status}</span>
                            <span class="list-item-badge">Prioritaet: ${task.priority}</span>
                            ${task.project_name ? `<span class="list-item-badge primary">${task.project_name}</span>` : ''}
                            ${task.due_date ? `<span class="list-item-badge">Faellig: ${new Date(task.due_date).toLocaleDateString()}</span>` : ''}
                            ${task.assigned_to ? `<span class="list-item-badge">@${task.assigned_to}</span>` : ''}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        ${task.status !== 'completed' ? `<button class="btn btn-success btn-small" onclick="completeTask(${task.id})">Erledigt</button>` : ''}
                        <button class="btn btn-danger btn-small" onclick="deleteTask(${task.id})">Delete</button>
                    </div>
                </div>
                ${task.description ? `<div class="list-item-content">${escapeHtml(task.description)}</div>` : ''}
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

async function loadProjectsForSelect() {
    try {
        const data = await api.listProjects({});
        const projects = data.projects || [];

        const selects = ['task-project-filter', 'task-project'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                const firstOption = id.includes('filter') ? '<option value="">Alle Projekte</option>' : '<option value="">-- Projekt waehlen --</option>';
                select.innerHTML = firstOption + projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
            }
        });
    } catch (error) {
        console.error('Failed to load projects for select:', error);
    }
}

function showTaskModal() {
    loadProjectsForSelect();
    document.getElementById('task-modal').style.display = 'flex';
}

function hideTaskModal() {
    document.getElementById('task-modal').style.display = 'none';
    document.getElementById('task-title').value = '';
    document.getElementById('task-description').value = '';
    document.getElementById('task-project').value = '';
    document.getElementById('task-priority').value = '5';
    document.getElementById('task-due-date').value = '';
    document.getElementById('task-assigned').value = '';
}

async function saveTask() {
    const title = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const project_id = document.getElementById('task-project').value;
    const priority = parseInt(document.getElementById('task-priority').value);
    const due_date = document.getElementById('task-due-date').value;
    const assigned_to = document.getElementById('task-assigned').value.trim();

    if (!title || !project_id) {
        showToast('Bitte Titel und Projekt eingeben', 'error');
        return;
    }

    try {
        const data = { title, project_id: parseInt(project_id), priority };
        if (description) data.description = description;
        if (due_date) data.due_date = due_date;
        if (assigned_to) data.assigned_to = assigned_to;

        const result = await api.request('/api/tasks', { method: 'POST', body: JSON.stringify(data) });
        if (result.success) {
            showToast('Task erstellt');
            hideTaskModal();
            loadTasks();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function completeTask(id) {
    try {
        const result = await api.request(`/api/tasks/${id}/complete`, { method: 'POST', body: '{}' });
        if (result.success) {
            showToast('Task erledigt');
            loadTasks();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteTask(id) {
    if (!confirm('Task wirklich loeschen?')) return;

    try {
        const result = await api.request(`/api/tasks/${id}`, { method: 'DELETE' });
        if (result.success) {
            showToast('Task geloescht');
            loadTasks();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Notes
// ============================================

async function loadNotes() {
    const container = document.getElementById('notes-list');
    container.innerHTML = '<div class="loading-state">Notes werden geladen...</div>';

    const typeFilter = document.getElementById('note-type-filter')?.value;
    const pinnedOnly = document.getElementById('note-pinned-filter')?.checked;
    const searchQuery = document.getElementById('note-search')?.value;

    try {
        const params = {};
        if (typeFilter) params.note_type = typeFilter;
        if (pinnedOnly) params.pinned_only = 'true';
        if (searchQuery) params.query = searchQuery;

        const query = new URLSearchParams(params);
        const data = await api.request(`/api/notes?${query}`);
        const notes = data.notes || [];

        if (notes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128221;</div>
                    <p>Keine Notes vorhanden</p>
                    <button class="btn btn-primary" onclick="showNoteModal()">Note erstellen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = notes.map(note => `
            <div class="list-item ${note.is_pinned ? 'pinned' : ''}">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${note.is_pinned ? '&#128204; ' : ''}${escapeHtml(note.title || 'Untitled')}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${note.note_type}</span>
                            ${(note.tags || []).map(t => `<span class="list-item-badge">${t}</span>`).join('')}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-danger btn-small" onclick="deleteNote(${note.id})">Delete</button>
                    </div>
                </div>
                <div class="list-item-content">${escapeHtml(note.content)}</div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showNoteModal() {
    document.getElementById('note-modal').style.display = 'flex';
}

function hideNoteModal() {
    document.getElementById('note-modal').style.display = 'none';
    document.getElementById('note-title').value = '';
    document.getElementById('note-content').value = '';
    document.getElementById('note-type').value = 'general';
    document.getElementById('note-pinned').checked = false;
    document.getElementById('note-tags').value = '';
}

async function saveNote() {
    const content = document.getElementById('note-content').value.trim();
    const title = document.getElementById('note-title').value.trim();
    const note_type = document.getElementById('note-type').value;
    const is_pinned = document.getElementById('note-pinned').checked;
    const tagsStr = document.getElementById('note-tags').value;
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

    if (!content) {
        showToast('Bitte Inhalt eingeben', 'error');
        return;
    }

    try {
        const data = { content, note_type, is_pinned, tags };
        if (title) data.title = title;

        const result = await api.request('/api/notes', { method: 'POST', body: JSON.stringify(data) });
        if (result.success) {
            showToast('Note erstellt');
            hideNoteModal();
            loadNotes();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteNote(id) {
    if (!confirm('Note wirklich loeschen?')) return;

    try {
        const result = await api.request(`/api/notes/${id}`, { method: 'DELETE' });
        if (result.success) {
            showToast('Note geloescht');
            loadNotes();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Triggers
// ============================================

async function loadTriggers() {
    const container = document.getElementById('triggers-list');
    container.innerHTML = '<div class="loading-state">Triggers werden geladen...</div>';

    const typeFilter = document.getElementById('trigger-type-filter')?.value;
    const activeFilter = document.getElementById('trigger-active-filter')?.value;

    try {
        const params = {};
        if (typeFilter) params.trigger_type = typeFilter;
        if (activeFilter) params.is_active = activeFilter;

        const query = new URLSearchParams(params);
        const data = await api.request(`/api/triggers?${query}`);
        const triggers = data.triggers || [];

        if (triggers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#9889;</div>
                    <p>Keine Triggers vorhanden</p>
                    <button class="btn btn-primary" onclick="showTriggerModal()">Trigger erstellen</button>
                </div>
            `;
            return;
        }

        container.innerHTML = triggers.map(trigger => `
            <div class="list-item">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(trigger.name)}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${trigger.trigger_type}</span>
                            <span class="list-item-badge">${trigger.action_type}</span>
                            ${trigger.is_active ? '<span class="list-item-badge success">Aktiv</span>' : '<span class="list-item-badge">Inaktiv</span>'}
                            ${trigger.event_source ? `<span class="list-item-badge">Quelle: ${trigger.event_source}</span>` : ''}
                            <span class="list-item-badge">Ausfuehrungen: ${trigger.trigger_count || 0}</span>
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-secondary btn-small" onclick="executeTriggerManually(${trigger.id})">Testen</button>
                        <button class="btn btn-danger btn-small" onclick="deleteTrigger(${trigger.id})">Delete</button>
                    </div>
                </div>
                ${trigger.description ? `<div class="list-item-content">${escapeHtml(trigger.description)}</div>` : ''}
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function showTriggerModal() {
    document.getElementById('trigger-modal').style.display = 'flex';
}

function hideTriggerModal() {
    document.getElementById('trigger-modal').style.display = 'none';
    document.getElementById('trigger-name').value = '';
    document.getElementById('trigger-description').value = '';
    document.getElementById('trigger-type').value = 'event';
    document.getElementById('trigger-event-source').value = 'conversation';
    document.getElementById('trigger-pattern').value = '';
    document.getElementById('trigger-action-type').value = 'execute_tool';
    document.getElementById('trigger-action-config').value = '';
}

async function saveTrigger() {
    const name = document.getElementById('trigger-name').value.trim();
    const description = document.getElementById('trigger-description').value.trim();
    const trigger_type = document.getElementById('trigger-type').value;
    const event_source = document.getElementById('trigger-event-source').value;
    const event_pattern = document.getElementById('trigger-pattern').value.trim();
    const action_type = document.getElementById('trigger-action-type').value;
    const action_config_str = document.getElementById('trigger-action-config').value.trim();

    if (!name || !action_config_str) {
        showToast('Bitte Name und Aktions-Konfiguration eingeben', 'error');
        return;
    }

    let action_config;
    try {
        action_config = JSON.parse(action_config_str);
    } catch (e) {
        showToast('Aktions-Konfiguration ist kein gueltiges JSON', 'error');
        return;
    }

    try {
        const data = { name, trigger_type, action_type, action_config };
        if (description) data.description = description;
        if (event_source) data.event_source = event_source;
        if (event_pattern) data.event_pattern = event_pattern;

        const result = await api.request('/api/triggers', { method: 'POST', body: JSON.stringify(data) });
        if (result.success) {
            showToast('Trigger erstellt');
            hideTriggerModal();
            loadTriggers();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function executeTriggerManually(id) {
    try {
        const result = await api.request(`/api/triggers/${id}/execute`, { method: 'POST', body: '{}' });
        if (result.success) {
            showToast('Trigger ausgefuehrt');
            loadTriggers();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteTrigger(id) {
    if (!confirm('Trigger wirklich loeschen?')) return;

    try {
        const result = await api.request(`/api/triggers/${id}`, { method: 'DELETE' });
        if (result.success) {
            showToast('Trigger geloescht');
            loadTriggers();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Conversations
// ============================================

let currentConversationSession = null;

async function loadConversations() {
    const container = document.getElementById('conversations-list');
    container.innerHTML = '<div class="loading-state">Konversationen werden geladen...</div>';

    const searchQuery = document.getElementById('conversation-search')?.value;
    const fromDate = document.getElementById('conversation-from-date')?.value;
    const toDate = document.getElementById('conversation-to-date')?.value;

    try {
        const params = {};
        if (searchQuery) params.query = searchQuery;
        if (fromDate) params.from_date = fromDate;
        if (toDate) params.to_date = toDate;

        const query = new URLSearchParams(params);
        const data = await api.request(`/api/conversations/search?${query}`);
        const conversations = data.conversations || [];

        if (conversations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#128172;</div>
                    <p>Keine Konversationen gefunden</p>
                </div>
            `;
            return;
        }

        container.innerHTML = conversations.map(conv => `
            <div class="list-item" onclick="showConversationDetail('${conv.session_id}')">
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${escapeHtml(conv.title || 'Conversation')}</div>
                        <div class="list-item-meta">
                            <span class="list-item-badge primary">${conv.message_count || 0} Nachrichten</span>
                            ${conv.client_name ? `<span class="list-item-badge">${conv.client_name}</span>` : ''}
                            ${conv.topics ? conv.topics.slice(0, 3).map(t => `<span class="list-item-badge">${t}</span>`).join('') : ''}
                            <span class="list-item-badge">${new Date(conv.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                </div>
                ${conv.summary ? `<div class="list-item-content">${escapeHtml(conv.summary.substring(0, 200))}...</div>` : ''}
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

async function showConversationDetail(sessionId) {
    currentConversationSession = sessionId;
    document.getElementById('conversation-modal').style.display = 'flex';
    document.getElementById('conversation-modal-title').textContent = `Konversation: ${sessionId.substring(0, 16)}...`;

    const messagesContainer = document.getElementById('conversation-messages');
    messagesContainer.innerHTML = '<div class="loading-state">Nachrichten werden geladen...</div>';

    try {
        const data = await api.request(`/api/conversations/${sessionId}/history`);
        const conv = data.conversation || {};
        const messages = conv.messages || [];

        if (messages.length === 0) {
            messagesContainer.innerHTML = '<div class="empty-state">Keine Nachrichten</div>';
            return;
        }

        messagesContainer.innerHTML = messages.map(msg => `
            <div class="conversation-message ${msg.role}">
                <div class="message-role">${msg.role === 'user' ? 'User' : 'Assistant'}</div>
                <div class="message-content">${escapeHtml(msg.content)}</div>
                <div class="message-time">${new Date(msg.created_at).toLocaleString()}</div>
            </div>
        `).join('');

    } catch (error) {
        messagesContainer.innerHTML = `<div class="empty-state">Fehler: ${error.message}</div>`;
    }
}

function hideConversationModal() {
    document.getElementById('conversation-modal').style.display = 'none';
    currentConversationSession = null;
}

async function summarizeCurrentConversation() {
    if (!currentConversationSession) return;

    const summaryText = prompt('Zusammenfassung eingeben:');
    if (!summaryText) return;

    try {
        const result = await api.request(`/api/conversations/${currentConversationSession}/summarize`, {
            method: 'POST',
            body: JSON.stringify({ summary_text: summaryText })
        });

        if (result.success) {
            showToast('Zusammenfassung gespeichert');
            hideConversationModal();
            loadConversations();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ============================================
// Utilities
// ============================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Theme
    new ThemeManager();

    // API Key
    const apiKeyInput = document.getElementById('api-key-input');
    if (apiKeyInput) {
        apiKeyInput.value = api.apiKey;
        apiKeyInput.addEventListener('change', (e) => {
            api.setAPIKey(e.target.value);
            loadDashboard();
        });
    }

    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Load initial data
    loadDashboard();

    // Auto-refresh
    setInterval(loadDashboard, 30000);

    console.log('Centre AI Dashboard initialized');
});
