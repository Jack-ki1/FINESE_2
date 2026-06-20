/**
 * FINESE2 Dashboard - Main Application Controller
 * SPA navigation, state management, and section rendering
 */

// ===== THEME MANAGEMENT (F1-inspired) =====
function initTheme() {
    const savedTheme = localStorage.getItem('finese2-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('finese2-theme', newTheme);
    updateThemeIcon(newTheme);
    
    showToast(`Switched to ${newTheme} mode`, 'info');
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-toggle i');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', initTheme);

// ===== COMMAND PALETTE (Ctrl+K) =====
function initCommandPalette() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+K or Cmd+K to open command palette
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            showCommandPalette();
        }
        
        // Escape to close
        if (e.key === 'Escape') {
            hideCommandPalette();
        }
    });
}

function showCommandPalette() {
    // Create palette if it doesn't exist
    let palette = document.getElementById('command-palette');
    if (!palette) {
        palette = createCommandPalette();
    }
    
    palette.classList.add('active');
    const input = palette.querySelector('.palette-input');
    if (input) {
        input.focus();
        input.select();
    }
}

function hideCommandPalette() {
    const palette = document.getElementById('command-palette');
    if (palette) {
        palette.classList.remove('active');
    }
}

function createCommandPalette() {
    const palette = document.createElement('div');
    palette.id = 'command-palette';
    palette.className = 'command-palette';
    
    palette.innerHTML = `
        <div class="palette-overlay" onclick="hideCommandPalette()"></div>
        <div class="palette-container">
            <div class="palette-header">
                <i class="fas fa-search"></i>
                <input type="text" class="palette-input" placeholder="Type a command..." oninput="filterCommands(this.value)">
                <kbd>ESC</kbd>
            </div>
            <div class="palette-results" id="palette-results">
                ${generateCommandItems()}
            </div>
        </div>
    `;
    
    document.body.appendChild(palette);
    return palette;
}

function generateCommandItems() {
    const commands = [
        { icon: '📊', label: 'Go to Dashboard', action: "navigateTo('dashboard')" },
        { icon: '📁', label: 'Upload Dataset', action: "navigateTo('data')" },
        { icon: '🔍', label: 'Run EDA Analysis', action: "navigateTo('eda')" },
        { icon: '🧹', label: 'Clean Data', action: "navigateTo('cleaning')" },
        { icon: '📈', label: 'Create Visualization', action: "navigateTo('visualization')" },
        { icon: '📉', label: 'Statistical Analysis', action: "navigateTo('statistics')" },
        { icon: '🤖', label: 'Train ML Model', action: "navigateTo('modeling')" },
        { icon: '⚙️', label: 'MLOps Settings', action: "navigateTo('mlops')" },
        { icon: '📝', label: 'Generate Report', action: "navigateTo('reports')" },
        { icon: '💬', label: 'AI Assistant', action: "navigateTo('ai')" },
        { icon: '🌙', label: 'Toggle Dark Mode', action: "toggleTheme()" },
        { icon: '⚡', label: 'Load Sample Data', action: "loadSampleDataset('iris')" },
    ];
    
    return commands.map((cmd, idx) => `
        <div class="palette-item" data-action="${cmd.action}" onclick="executeCommand('${cmd.action}')">
            <span class="palette-icon">${cmd.icon}</span>
            <span class="palette-label">${cmd.label}</span>
            <span class="palette-shortcut">${idx < 9 ? `<kbd>${idx + 1}</kbd>` : ''}</span>
        </div>
    `).join('');
}

function filterCommands(query) {
    const items = document.querySelectorAll('.palette-item');
    const lowerQuery = query.toLowerCase();
    
    items.forEach(item => {
        const label = item.querySelector('.palette-label').textContent.toLowerCase();
        item.style.display = label.includes(lowerQuery) ? 'flex' : 'none';
    });
}

function executeCommand(action) {
    hideCommandPalette();
    eval(action);
}

// Initialize command palette
document.addEventListener('DOMContentLoaded', initCommandPalette);

// ===== LOADING OVERLAY (F1-inspired) =====
const SIM_MSGS = [
    'Computing statistics…',
    'Analyzing data patterns…',
    'Running models…',
    'Generating insights…',
    'Finishing up…',
];

let _simInterval = null;

function showLoading(message = 'Processing...') {
    // Clear any existing interval
    if (_simInterval) {
        clearInterval(_simInterval);
        _simInterval = null;
    }
    
    const overlay = document.getElementById('loadingOverlay');
    const msgEl = document.getElementById('loadingMessage');
    
    if (msgEl) msgEl.textContent = message;
    if (overlay) overlay.classList.add('active');
    
    // Cycle through messages for long operations
    let idx = 0;
    _simInterval = setInterval(() => {
        idx++;
        if (idx >= SIM_MSGS.length) {
            clearInterval(_simInterval);
            _simInterval = null;
            return;
        }
        if (msgEl) msgEl.textContent = SIM_MSGS[idx];
    }, 800);
}

function hideLoading() {
    if (_simInterval) {
        clearInterval(_simInterval);
        _simInterval = null;
    }
    
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

// ===== ENHANCED NOTIFICATION SYSTEM (from F1 Dashboard) =====
let toastQueue = [];

function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-msg">${message}</span>
        <span class="toast-close" onclick="this.parentElement.remove()">×</span>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 350);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Legacy support - redirect to new system
function showNotification(message, type = 'info', duration = 4000) {
    showToast(message, type, duration);
}

// ===== APPLICATION STATE =====
const AppState = {
    currentSection: 'dashboard',
    hasData: false,
    dataInfo: null,
    columns: [],
    numericColumns: [],
    categoricalColumns: [],
};

// ===== NAVIGATION =====
function switchSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

    // Show target section
    const section = document.getElementById(sectionId);
    const tab = document.querySelector(`[data-section="${sectionId}"]`);
    if (section) section.classList.add('active');
    if (tab) tab.classList.add('active');

    AppState.currentSection = sectionId;

    // Load section data
    loadSectionData(sectionId);
}

async function loadSectionData(sectionId) {
    if (!AppState.hasData && sectionId !== 'dashboard' && sectionId !== 'ai') {
        showNotification('Please upload a dataset first', 'warning');
        switchSection('dashboard');
        return;
    }

    switch (sectionId) {
        case 'dashboard': await loadDashboard(); break;
        case 'data': await loadDataSection(); break;
        case 'eda': await loadEDASection(); break;
        case 'cleaning': await loadCleaningSection(); break;
        case 'visualization': await loadVisualizationSection(); break;
        case 'analysis': await loadAnalysisSection(); break;
        case 'modeling': await loadModelingSection(); break;
        case 'mlops': await loadMLOpsSection(); break;
        case 'reports': await loadReportsSection(); break;
        case 'ai': ai.init('chat-messages', 'chat-input'); break;
    }
}

// ===== DASHBOARD SECTION =====
async function loadDashboard() {
    const container = document.getElementById('dashboard-content');
    if (!AppState.hasData) {
        // Enhanced empty state with hero section (from F1 Dashboard)
        container.innerHTML = `
            <div class="hero-section">
                <div class="hero-content">
                    <div class="hero-eyebrow">Data Intelligence Platform</div>
                    <h1>Welcome to <span class="accent-text">FINESE2</span></h1>
                    <p class="hero-subtitle">Your advanced analytics and machine learning workspace</p>
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-value">∞</div>
                            <div class="kpi-label">Datasets</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-value">ML</div>
                            <div class="kpi-label">Models</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-value">AI</div>
                            <div class="kpi-label">Assistant</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-value">EDA</div>
                            <div class="kpi-label">Analysis</div>
                        </div>
                    </div>
                </div>
                <div class="hero-actions">
                    <button class="btn-enhanced btn-primary-enhanced" onclick="switchSection('data')">
                        <i class="fas fa-upload"></i> Upload Dataset
                    </button>
                    <div style="margin-top: 1rem; display: flex; gap: 0.8rem; justify-content: center;">
                        <button class="btn-enhanced btn-secondary-enhanced" onclick="loadSampleDataset('iris')">🌸 Iris</button>
                        <button class="btn-enhanced btn-secondary-enhanced" onclick="loadSampleDataset('titanic')">🚢 Titanic</button>
                        <button class="btn-enhanced btn-secondary-enhanced" onclick="loadSampleDataset('wine')">🍷 Wine</button>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    try {
        const info = await api.getDataInfo();
        AppState.dataInfo = info;
        
        // Enhanced dashboard with hero and KPI cards (from F1 Dashboard)
        container.innerHTML = `
            <div class="hero-section-enhanced">
                <div class="hero-header">
                    <div class="hero-badge"><i class="fas fa-database"></i> Data Loaded</div>
                    <h1>${info.file_name || 'Dataset'}</h1>
                    <p class="hero-sub">${info.shape?.[0]?.toLocaleString() || 0} rows · ${info.shape?.[1] || 0} columns</p>
                </div>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">${(info.rows || info.shape?.[0] || 0).toLocaleString()}</div>
                        <div class="kpi-label">Total Rows</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${info.columns?.length || info.shape?.[1] || 0}</div>
                        <div class="kpi-label">Columns</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${info.numeric_columns?.length || 0}</div>
                        <div class="kpi-label">Numeric Features</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${info.missing_values?.toLocaleString() || 0}</div>
                        <div class="kpi-label">Missing Values</div>
                    </div>
                </div>
            </div>
            
            <div class="grid-2">
                <div class="card-enhanced">
                    <div class="card-header"><span class="card-title">📊 Data Types Distribution</span></div>
                    <div id="chart-dtypes"></div>
                </div>
                <div class="card-enhanced">
                    <div class="card-header"><span class="card-title">📈 Numeric Overview</span></div>
                    <div id="chart-overview"></div>
                </div>
            </div>
        `;

        // Render dtype chart
        if (info.dtypes) {
            const dtypeCounts = {};
            Object.values(info.dtypes).forEach(t => { dtypeCounts[t] = (dtypeCounts[t] || 0) + 1; });
            charts.pieChart('chart-dtypes', Object.keys(dtypeCounts), Object.values(dtypeCounts), 'Data Types');
        }
    } catch (error) {
        container.innerHTML = `<div class="card"><p style="color: var(--danger);">Error loading dashboard: ${error.message}</p></div>`;
    }
}

async function loadSampleDataset(name) {
    showLoading(true);
    try {
        const result = await api.loadSampleDataset(name);
        AppState.hasData = true;
        AppState.columns = result.columns || [];
        // Infer column types from dtypes map
        if (result.dtypes) {
            AppState.numericColumns = Object.entries(result.dtypes)
                .filter(([, t]) => ['int64','float64','int32','float32'].some(nt => t.includes(nt)))
                .map(([col]) => col);
            AppState.categoricalColumns = AppState.columns.filter(c => !AppState.numericColumns.includes(c));
        }
        showNotification(`Loaded ${name} dataset successfully!`, 'success');
        loadDashboard();
    } catch (error) {
        showNotification('Failed to load sample: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== DATA SECTION =====
async function loadDataSection() {
    const container = document.getElementById('data-content');
    container.innerHTML = `
        <div class="card">
            <div class="card-header"><span class="card-title">📁 Upload Dataset</span></div>
            <div class="upload-zone" id="upload-zone">
                <div class="upload-icon">📤</div>
                <div class="upload-text">Drop your file here or click to browse</div>
                <div class="upload-hint">Supports CSV, Excel, JSON, Parquet</div>
            </div>
            <input type="file" id="file-input" accept=".csv,.xlsx,.xls,.json,.parquet" style="display:none">
        </div>
        <div id="data-preview"></div>
    `;

    // Setup click handler for upload zone
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    
    zone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Setup file input change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            uploadFile(e.target.files[0]);
            // Reset input so same file can be selected again
            e.target.value = '';
        }
    });

    // Setup drag & drop
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault(); zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });

    if (AppState.hasData) {
        const sample = await api.getDataSample(50);
        renderDataTable('data-preview', sample);
    }
}

async function uploadFile(file) {
    showLoading(true);
    try {
        const result = await api.uploadFile(file);
        AppState.hasData = true;
        AppState.columns = result.columns || [];
        // Infer column types from dtypes map
        if (result.dtypes) {
            AppState.numericColumns = Object.entries(result.dtypes)
                .filter(([, t]) => ['int64','float64','int32','float32'].some(nt => t.includes(nt)))
                .map(([col]) => col);
            AppState.categoricalColumns = AppState.columns.filter(c => !AppState.numericColumns.includes(c));
        }
        showNotification(`Uploaded ${file.name} successfully!`, 'success');
        loadDataSection();
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function renderDataTable(containerId, data) {
    const container = document.getElementById(containerId);
    if (!data) {
        container.innerHTML = '<div class="card"><p>No data available</p></div>';
        return;
    }
    
    // Handle both {columns, data} and {columns, preview} shapes
    const columns = data.columns || [];
    const rows = data.data || data.preview || [];
    
    if (!columns.length || !rows.length) {
        container.innerHTML = '<div class="card"><p>No data to display</p></div>';
        return;
    }
    
    let html = '<div class="card"><div class="card-header"><span class="card-title">📋 Data Preview</span></div><div style="overflow-x:auto;"><table class="data-table"><thead><tr>';
    columns.forEach(col => { html += `<th>${col}</th>`; });
    html += '</tr></thead><tbody>';
    rows.forEach(row => {
        html += '<tr>';
        columns.forEach(col => { html += `<td>${row[col] !== null && row[col] !== undefined ? row[col] : ''}</td>`; });
        html += '</tr>';
    });
    html += '</tbody></table></div></div>';
    container.innerHTML = html;
}

// ===== EDA SECTION =====
async function loadEDASection() {
    const container = document.getElementById('eda-content');
    container.innerHTML = `
        <div class="inner-tabs">
            <button class="inner-tab active" onclick="loadEDATab('profile', this)">📊 Profile</button>
            <button class="inner-tab" onclick="loadEDATab('distribution', this)">📈 Distributions</button>
            <button class="inner-tab" onclick="loadEDATab('correlation', this)">🔗 Correlations</button>
            <button class="inner-tab" onclick="loadEDATab('missing', this)">❓ Missing Values</button>
        </div>
        <div id="eda-tab-content"></div>
    `;
    loadEDATab('profile');
}

async function loadEDATab(tab, el = null) {
    document.querySelectorAll('#eda-content .inner-tab').forEach(t => t.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        // Fallback: find and activate the button matching the tab name
        const buttons = document.querySelectorAll('#eda-content .inner-tab');
        buttons.forEach(btn => {
            if (btn.textContent.toLowerCase().includes(tab)) {
                btn.classList.add('active');
            }
        });
    }

    const content = document.getElementById('eda-tab-content');
    content.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>';

    try {
        switch (tab) {
            case 'profile':
                const profile = await api.getProfile();
                content.innerHTML = `<div class="card"><div class="card-header"><span class="card-title">Data Profile</span></div><pre style="color:var(--text-secondary);font-size:13px;overflow:auto;">${JSON.stringify(profile, null, 2)}</pre></div>`;
                break;
            case 'distribution':
                content.innerHTML = `
                    <div class="card">
                        <div class="form-group">
                            <label class="form-label">Select Column</label>
                            <select class="form-select" id="dist-column" onchange="renderDistribution()">
                                ${AppState.columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="chart-container" id="dist-chart"></div>
                `;
                renderDistribution();
                break;
            case 'correlation':
                const corr = await api.getCorrelation();
                if (corr) {
                    content.innerHTML = '<div class="chart-container" id="corr-chart"></div>';
                    charts.renderPlotlyJSON('corr-chart', corr);
                } else {
                    content.innerHTML = '<div class="card"><p>Not enough numeric columns for correlation analysis.</p></div>';
                }
                break;
            case 'missing':
                const missing = await api.getMissingValues();
                content.innerHTML = `<div class="card"><div class="card-header"><span class="card-title">Missing Values</span></div><pre style="color:var(--text-secondary);font-size:13px;">${JSON.stringify(missing, null, 2)}</pre></div>`;
                break;
        }
    } catch (error) {
        content.innerHTML = `<div class="card"><p style="color:var(--danger);">Error: ${error.message}</p></div>`;
    }
}

async function renderDistribution() {
    const col = document.getElementById('dist-column')?.value;
    if (!col) return;
    try {
        const dist = await api.getDistribution(col);
        if (dist && dist.chart_json) {
            charts.renderPlotlyJSON('dist-chart', dist.chart_json);
        }
    } catch (error) {
        console.error('Distribution error:', error);
    }
}

// ===== CLEANING SECTION =====
async function loadCleaningSection() {
    const container = document.getElementById('cleaning-content');
    container.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>';

    try {
        const recs = await api.getCleaningRecommendations();
        let html = '<div class="card"><div class="card-header"><span class="card-title">🧹 Cleaning Recommendations</span></div>';

        if (recs && recs.missing && recs.missing.length > 0) {
            html += '<h4 style="margin:16px 0 8px;">Missing Values</h4>';
            recs.missing.forEach(r => {
                html += `<div style="padding:8px;border-bottom:1px solid var(--border);"><span class="badge badge-warning">${r.priority}</span> <strong>${r.column}</strong>: ${r.issue} → <em>${r.action}</em></div>`;
            });
        }

        if (recs && recs.duplicates && recs.duplicates.length > 0) {
            html += '<h4 style="margin:16px 0 8px;">Duplicates</h4>';
            recs.duplicates.forEach(r => {
                html += `<div style="padding:8px;border-bottom:1px solid var(--border);"><span class="badge badge-danger">${r.priority}</span> ${r.issue} → <em>${r.action}</em></div>`;
            });
        }

        html += `<div style="margin-top:20px;display:flex;gap:12px;">
            <button class="btn btn-primary" onclick="autoClean(false)">🧹 Auto Clean</button>
            <button class="btn btn-danger" onclick="autoClean(true)">⚡ Aggressive Clean</button>
        </div></div>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="card"><p style="color:var(--danger);">Error: ${error.message}</p></div>`;
    }
}

async function autoClean(aggressive) {
    showLoading(true);
    try {
        const result = await api.autoClean(aggressive);
        showNotification(`Cleaned! ${result.log?.steps_applied || 0} steps applied.`, 'success');
    } catch (error) {
        showNotification('Cleaning failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== VISUALIZATION SECTION =====
async function loadVisualizationSection() {
    const container = document.getElementById('viz-content');
    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><span class="card-title">📊 Chart Builder</span></div>
                <div class="form-group">
                    <label class="form-label">Chart Type</label>
                    <select class="form-select" id="viz-type">
                        <option value="bar">Bar Chart</option>
                        <option value="line">Line Chart</option>
                        <option value="scatter">Scatter Plot</option>
                        <option value="histogram">Histogram</option>
                        <option value="box">Box Plot</option>
                        <option value="pie">Pie Chart</option>
                        <option value="heatmap">Heatmap</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">X Axis</label>
                    <select class="form-select" id="viz-x">${AppState.columns.map(c => `<option value="${c}">${c}</option>`).join('')}</select>
                </div>
                <div class="form-group">
                    <label class="form-label">Y Axis</label>
                    <select class="form-select" id="viz-y">${AppState.columns.map(c => `<option value="${c}">${c}</option>`).join('')}</select>
                </div>
                <button class="btn btn-primary" onclick="createVisualization()">🎨 Generate Chart</button>
            </div>
            <div class="chart-container" id="viz-chart" style="min-height:400px;">
                <div class="empty-state"><div class="empty-icon">📊</div><h3>Select options and generate</h3></div>
            </div>
        </div>
    `;
}

async function createVisualization() {
    const chartType = document.getElementById('viz-type').value;
    const x = document.getElementById('viz-x').value;
    const y = document.getElementById('viz-y').value;
    showLoading(true);
    try {
        const result = await api.createChart(chartType, { x, y });
        if (result && result.chart_json) {
            charts.renderPlotlyJSON('viz-chart', result.chart_json);
        }
    } catch (error) {
        showNotification('Chart error: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== ANALYSIS SECTION =====
async function loadAnalysisSection() {
    const container = document.getElementById('analysis-content');
    container.innerHTML = `
        <div class="inner-tabs">
            <button class="inner-tab active" onclick="loadAnalysisTab('summary', this)">📊 Summary</button>
            <button class="inner-tab" onclick="loadAnalysisTab('hypothesis', this)">🧪 Hypothesis Tests</button>
            <button class="inner-tab" onclick="loadAnalysisTab('regression', this)">📈 Regression</button>
        </div>
        <div id="analysis-tab-content"></div>
    `;
    loadAnalysisTab('summary');
}

async function loadAnalysisTab(tab, el = null) {
    document.querySelectorAll('#analysis-content .inner-tab').forEach(t => t.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        const buttons = document.querySelectorAll('#analysis-content .inner-tab');
        buttons.forEach(btn => {
            if (btn.textContent.toLowerCase().includes(tab)) {
                btn.classList.add('active');
            }
        });
    }
    const content = document.getElementById('analysis-tab-content');

    try {
        if (tab === 'summary') {
            const stats = await api.getSummaryStats(AppState.columns);
            let html = '<div class="card"><div class="card-header"><span class="card-title">Summary Statistics</span></div><div style="overflow-x:auto;"><table class="data-table"><thead><tr><th>Column</th><th>Mean</th><th>Std</th><th>Min</th><th>Max</th><th>Missing</th></tr></thead><tbody>';
            if (stats) {
                Object.entries(stats).forEach(([col, s]) => {
                    html += `<tr><td>${col}</td><td>${s.mean?.toFixed(2) || '-'}</td><td>${s.std?.toFixed(2) || '-'}</td><td>${s.min?.toFixed(2) || '-'}</td><td>${s.max?.toFixed(2) || '-'}</td><td>${s.missing || 0}</td></tr>`;
                });
            }
            html += '</tbody></table></div></div>';
            content.innerHTML = html;
        } else if (tab === 'hypothesis') {
            content.innerHTML = `
                <div class="card">
                    <div class="form-group"><label class="form-label">Test Type</label>
                        <select class="form-select" id="hyp-test"><option value="t_test">T-Test</option><option value="anova">ANOVA</option><option value="chi_square">Chi-Square</option></select>
                    </div>
                    <div class="form-group"><label class="form-label">Column 1</label><select class="form-select" id="hyp-col1">${AppState.columns.map(c => `<option>${c}</option>`).join('')}</select></div>
                    <div class="form-group"><label class="form-label">Group Column (optional)</label><select class="form-select" id="hyp-col2"><option value="">None</option>${AppState.columns.map(c => `<option>${c}</option>`).join('')}</select></div>
                    <button class="btn btn-primary" onclick="runHypothesisTest()">🧪 Run Test</button>
                    <div id="hyp-result" style="margin-top:16px;"></div>
                </div>
            `;
        } else if (tab === 'regression') {
            content.innerHTML = `
                <div class="card">
                    <div class="form-group"><label class="form-label">Dependent Variable (Y)</label><select class="form-select" id="reg-y">${AppState.columns.map(c => `<option>${c}</option>`).join('')}</select></div>
                    <div class="form-group"><label class="form-label">Independent Variables (X)</label><select class="form-select" id="reg-x" multiple style="height:120px;">${AppState.columns.map(c => `<option>${c}</option>`).join('')}</select></div>
                    <button class="btn btn-primary" onclick="runRegression()">📈 Run Regression</button>
                    <div id="reg-result" style="margin-top:16px;"></div>
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `<div class="card"><p style="color:var(--danger);">Error: ${error.message}</p></div>`;
    }
}

async function runHypothesisTest() {
    showLoading(true);
    try {
        const testType = document.getElementById('hyp-test').value;
        const col1 = document.getElementById('hyp-col1').value;
        const col2 = document.getElementById('hyp-col2').value;
        const result = await api.hypothesisTest(testType, { column1: col1, group_column: col2 || undefined });
        document.getElementById('hyp-result').innerHTML = `<div class="card"><pre style="color:var(--text-secondary);font-size:13px;">${JSON.stringify(result, null, 2)}</pre></div>`;
    } catch (error) {
        showNotification('Test failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function runRegression() {
    showLoading(true);
    try {
        const dep = document.getElementById('reg-y').value;
        const indep = Array.from(document.getElementById('reg-x').selectedOptions).map(o => o.value);
        if (indep.length === 0) { showNotification('Select at least one independent variable', 'warning'); return; }
        const result = await api.regressionAnalysis(dep, indep);
        document.getElementById('reg-result').innerHTML = `<div class="card"><pre style="color:var(--text-secondary);font-size:13px;">${JSON.stringify(result, null, 2)}</pre></div>`;
    } catch (error) {
        showNotification('Regression failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== MODELING SECTION =====
async function loadModelingSection() {
    const container = document.getElementById('modeling-content');
    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><span class="card-title">🤖 AutoML Training</span></div>
                <div class="form-group"><label class="form-label">Target Column</label><select class="form-select" id="ml-target">${AppState.columns.map(c => `<option>${c}</option>`).join('')}</select></div>
                <div class="form-group"><label class="form-label">Problem Type</label><select class="form-select" id="ml-problem"><option value="">Auto-detect</option><option value="classification">Classification</option><option value="regression">Regression</option></select></div>
                <button class="btn btn-primary" onclick="trainModels()">🚀 Train Models</button>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">📊 Results</span></div>
                <div id="ml-results"><div class="empty-state"><div class="empty-icon">🤖</div><h3>Train models to see results</h3></div></div>
            </div>
        </div>
    `;
}

async function trainModels() {
    showLoading(true);
    try {
        const target = document.getElementById('ml-target').value;
        const problemType = document.getElementById('ml-problem').value || undefined;
        const result = await api.trainModels(target, problemType);
        if (result && result.models) {
            const modelNames = Object.keys(result.models);
            const metrics = modelNames.map(m => result.models[m].metrics);
            document.getElementById('ml-results').innerHTML = `<div id="ml-chart"></div><p style="margin-top:12px;color:var(--text-secondary);">Best model: <strong style="color:var(--accent);">${result.best_model}</strong></p>`;
            if (modelNames.length > 0) {
                charts.modelComparison('ml-chart', modelNames, metrics);
            }
        }
    } catch (error) {
        showNotification('Training failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== MLOPS SECTION =====
async function loadMLOpsSection() {
    const container = document.getElementById('mlops-content');
    container.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>';
    try {
        const leaderboard = await api.getLeaderboard();
        let html = '<div class="card"><div class="card-header"><span class="card-title">🏆 Model Leaderboard</span></div>';
        if (leaderboard && leaderboard.length > 0) {
            html += '<table class="data-table"><thead><tr><th>Model</th><th>Experiment</th><th>Metrics</th><th>Date</th></tr></thead><tbody>';
            leaderboard.forEach(r => {
                html += `<tr><td>${r.model}</td><td>${r.experiment || '-'}</td><td><pre style="font-size:11px;">${JSON.stringify(r.metrics, null, 1)}</pre></td><td>${r.created_at || '-'}</td></tr>`;
            });
            html += '</tbody></table>';
        } else {
            html += '<div class="empty-state"><div class="empty-icon">🏆</div><h3>No experiments yet</h3><p>Train models to see them here</p></div>';
        }
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="card"><p style="color:var(--danger);">Error: ${error.message}</p></div>`;
    }
}

// ===== REPORTS SECTION =====
async function loadReportsSection() {
    const container = document.getElementById('reports-content');
    container.innerHTML = `
        <div class="card">
            <div class="card-header"><span class="card-title">📝 Generate Report</span></div>
            <div class="form-group"><label class="form-label">Report Title</label><input class="form-input" id="report-title" value="FINESE2 Data Analysis Report"></div>
            <div class="form-group"><label class="form-label">Format</label>
                <select class="form-select" id="report-format"><option value="html">HTML</option><option value="excel">Excel</option><option value="markdown">Markdown</option></select>
            </div>
            <button class="btn btn-primary" onclick="generateReport()">📝 Generate Report</button>
            <div id="report-result" style="margin-top:16px;"></div>
        </div>
    `;
}

async function generateReport() {
    showLoading(true);
    try {
        const title = document.getElementById('report-title').value;
        const format = document.getElementById('report-format').value;
        const result = await api.generateReport(format, title);
        if (result && result.download_url) {
            document.getElementById('report-result').innerHTML = `<a href="${result.download_url}" class="btn btn-primary" download>📥 Download Report</a>`;
        } else if (result && result.content) {
            document.getElementById('report-result').innerHTML = `<div style="max-height:400px;overflow:auto;background:var(--bg-secondary);padding:16px;border-radius:8px;"><pre style="font-size:12px;">${result.content.substring(0, 5000)}...</pre></div>`;
        }
        showNotification('Report generated!', 'success');
    } catch (error) {
        showNotification('Report failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    // Setup navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchSection(tab.dataset.section));
    });

    // Load initial section
    loadDashboard();
});
