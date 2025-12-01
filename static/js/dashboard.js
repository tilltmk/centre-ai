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
        case 'tools': loadTools(); break;
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
