/**
 * FINESE2 Dashboard — Main Application Controller v4.0
 * SPA navigation, state management, and section rendering.
 *
 * ⚠️  Business logic & API calls are UNCHANGED.
 *     Only UI rendering (HTML strings, class names) has been updated
 *     to match the new Deep Space design system.
 */

/* ═══════════════════════════════════════════════════════════════
   THEME
   ═══════════════════════════════════════════════════════════════ */
function initTheme () {
  const saved = localStorage.getItem('finese2-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  _updateThemeIcon(saved);
}

function toggleTheme () {
  const current = document.documentElement.getAttribute('data-theme');
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('finese2-theme', next);
  _updateThemeIcon(next);
  showToast(`Switched to ${next} mode`, 'info');
}

function _updateThemeIcon (theme) {
  const icon = document.querySelector('#theme-toggle i');
  if (icon) icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
}

document.addEventListener('DOMContentLoaded', initTheme);


/* ═══════════════════════════════════════════════════════════════
   APPLICATION STATE
   ═══════════════════════════════════════════════════════════════ */
const AppState = {
  currentSection:     'dashboard',
  hasData:            false,
  dataInfo:           null,
  columns:            [],
  numericColumns:     [],
  categoricalColumns: [],
  selectedChartType:  'bar',
};


/* ═══════════════════════════════════════════════════════════════
   NAVIGATION
   ═══════════════════════════════════════════════════════════════ */
function navigateTo (sectionId, navButton = null) {
  /* hide all sections */
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

  /* deactivate all nav items */
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  /* show target section */
  const section = document.getElementById(`section-${sectionId}`);
  if (section) {
    section.classList.add('active');
  } else {
    console.error(`Section not found: section-${sectionId}`);
    return;
  }

  /* activate nav button */
  if (navButton) {
    navButton.classList.add('active');
  } else {
    const btn = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
    if (btn) btn.classList.add('active');
  }

  AppState.currentSection = sectionId;
  loadSectionData(sectionId);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* legacy alias */
function switchSection (sectionId) { navigateTo(sectionId); }


/* ═══════════════════════════════════════════════════════════════
   SECTION ROUTER
   ═══════════════════════════════════════════════════════════════ */
async function loadSectionData (sectionId) {
  if (!AppState.hasData && sectionId !== 'dashboard' && sectionId !== 'ai') {
    showToast('Please upload or load a dataset first', 'warning');
    navigateTo('dashboard');
    return;
  }

  switch (sectionId) {
    case 'dashboard':    await loadDashboard();              break;
    case 'data':         await loadDataSection();             break;
    case 'eda':          await loadEDASection();              break;
    case 'cleaning':     await loadCleaningSection();         break;
    case 'visualization':await loadVisualizationSection();    break;
    case 'analysis':     await loadAnalysisSection();         break;
    case 'modeling':     await loadModelingSection();         break;
    case 'mlops':        await loadMLOps();                   break;
    case 'reports':      await loadReportsSection();          break;
    case 'ai':           ai.init('chat-messages', 'chat-input'); break;
  }
}


/* ═══════════════════════════════════════════════════════════════
   COMMAND PALETTE
   ═══════════════════════════════════════════════════════════════ */
function openCommandPalette () {
  const overlay = document.getElementById('cmd-overlay');
  const input   = document.getElementById('cmd-input');
  if (!overlay) return;
  overlay.classList.remove('hidden');
  if (input) setTimeout(() => { input.focus(); input.select(); }, 80);
  populateCommandPalette();
}

function closeCommandPalette () {
  const overlay = document.getElementById('cmd-overlay');
  if (overlay) overlay.classList.add('hidden');
}

function closePaletteOnBg (event) {
  if (event.target.id === 'cmd-overlay') closeCommandPalette();
}

function populateCommandPalette () {
  const results = document.getElementById('cmd-results');
  if (!results) return;

  const commands = [
    { icon: 'fa-solid fa-chart-tree-map', label: 'Dashboard',            shortcut: '',   action: "navigateTo('dashboard')" },
    { icon: 'fa-solid fa-database',       label: 'Upload dataset',       shortcut: '',   action: "navigateTo('data')" },
    { icon: 'fa-solid fa-chart-area',     label: 'Run EDA analysis',     shortcut: '',   action: "navigateTo('eda')" },
    { icon: 'fa-solid fa-broom',          label: 'Clean data',           shortcut: '',   action: "navigateTo('cleaning')" },
    { icon: 'fa-solid fa-chart-column',   label: 'Create visualization', shortcut: '',   action: "navigateTo('visualization')" },
    { icon: 'fa-solid fa-flask',          label: 'Statistical analysis', shortcut: '',   action: "navigateTo('analysis')" },
    { icon: 'fa-solid fa-microchip',      label: 'Train ML models',      shortcut: '',   action: "navigateTo('modeling')" },
    { icon: 'fa-solid fa-gauge-high',     label: 'MLOps & experiments',  shortcut: '',   action: "navigateTo('mlops')" },
    { icon: 'fa-solid fa-file-chart-column', label: 'Generate report',   shortcut: '',   action: "navigateTo('reports')" },
    { icon: 'fa-solid fa-robot',          label: 'AI Assistant',         shortcut: '',   action: "navigateTo('ai')" },
    { icon: 'fa-solid fa-circle-half-stroke', label: 'Toggle theme',     shortcut: '⌘T', action: 'toggleTheme()' },
    { icon: 'fa-solid fa-upload',         label: 'Load Iris sample',     shortcut: '',   action: "loadSampleDataset('iris')" },
    { icon: 'fa-solid fa-upload',         label: 'Load Titanic sample',  shortcut: '',   action: "loadSampleDataset('titanic')" },
    { icon: 'fa-solid fa-upload',         label: 'Load Wine sample',     shortcut: '',   action: "loadSampleDataset('wine')" },
  ];

  results.innerHTML = commands.map(cmd => `
    <li class="cmd-item" role="option" onclick="${cmd.action}; closeCommandPalette()">
      <i class="${cmd.icon}"></i>
      <span class="cmd-label">${cmd.label}</span>
      ${cmd.shortcut ? `<kbd>${cmd.shortcut}</kbd>` : ''}
    </li>
  `).join('');
}

function filterCommands (query) {
  const items = document.querySelectorAll('.cmd-item');
  const q     = query.toLowerCase();
  items.forEach(item => {
    const label = item.querySelector('.cmd-label').textContent.toLowerCase();
    item.style.display = label.includes(q) ? 'flex' : 'none';
  });
}

function cmdKeydown (event) {
  if (event.key === 'Escape') closeCommandPalette();
}

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    openCommandPalette();
  }
  if (e.key === 'Escape') {
    closeCommandPalette();
    closeAIConfig();
  }
});


/* ═══════════════════════════════════════════════════════════════
   LOADING VEIL
   ═══════════════════════════════════════════════════════════════ */
const _LOADING_MSGS = [
  'Computing statistics…',
  'Analysing patterns…',
  'Running models…',
  'Generating insights…',
  'Almost done…',
];

let _simInterval = null;

function showLoading (message = 'Processing…') {
  if (_simInterval) { clearInterval(_simInterval); _simInterval = null; }

  const veil  = document.getElementById('loading-veil');
  const msgEl = document.getElementById('loading-msg');

  if (msgEl) msgEl.textContent = message;
  if (veil)  { veil.classList.remove('hidden'); veil.setAttribute('aria-hidden', 'false'); }

  let idx = 0;
  _simInterval = setInterval(() => {
    idx++;
    if (idx >= _LOADING_MSGS.length) { clearInterval(_simInterval); _simInterval = null; return; }
    if (msgEl) msgEl.textContent = _LOADING_MSGS[idx];
  }, 900);
}

function hideLoading () {
  if (_simInterval) { clearInterval(_simInterval); _simInterval = null; }
  const veil = document.getElementById('loading-veil');
  if (veil)  { veil.classList.add('hidden'); veil.setAttribute('aria-hidden', 'true'); }
}


/* ═══════════════════════════════════════════════════════════════
   TOAST SYSTEM
   ═══════════════════════════════════════════════════════════════ */
function showToast (message, type = 'info', duration = 3600) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: 'fa-check-circle', error: 'fa-circle-xmark',
                   warning: 'fa-triangle-exclamation', info: 'fa-circle-info' };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${icons[type] || icons.info} toast-icon"></i>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add('show')));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 380);
  }, duration);
}

/* legacy alias */
function showNotification (message, type = 'info', duration = 4000) {
  showToast(message, type, duration);
}


/* ═══════════════════════════════════════════════════════════════
   DATA STATUS PILL
   ═══════════════════════════════════════════════════════════════ */
function _updateDataStatus (active, label) {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-label');
  if (dot)  { dot.className  = `status-dot ${active ? 'dot-active' : 'dot-idle'}`; }
  if (text) { text.textContent = label; }
}


/* ═══════════════════════════════════════════════════════════════
   DASHBOARD SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadDashboard () {
  if (!AppState.hasData) {
    _showHeroEmpty();
    hideLoading();
    return;
  }

  showLoading('Loading dashboard…');
  try {
    const info = await api.getDataInfo();
    AppState.dataInfo = info;
    _showDashLoaded(info);
  } catch (err) {
    console.error('Dashboard load error:', err);
    showToast('Error loading dashboard: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

function _showHeroEmpty () {
  document.getElementById('hero-empty')?.classList.remove('hidden');
  document.getElementById('dash-loaded')?.classList.add('hidden');
}

function _showDashLoaded (info) {
  document.getElementById('hero-empty')?.classList.add('hidden');
  const loaded = document.getElementById('dash-loaded');
  if (loaded) loaded.classList.remove('hidden');

  /* KPI tiles */
  const rows    = (info.rows    ?? info.shape?.[0] ?? 0);
  const cols    = (info.columns?.length ?? info.shape?.[1] ?? 0);
  const numeric = info.numeric_columns?.length ?? 0;
  const missing = Object.values(info.missing || {}).reduce((a,b) => a+b, 0);
  const dups    = info.duplicates ?? 0;
  const memKb   = info.memory_usage ? (info.memory_usage / 1024).toFixed(1) + ' KB' : '—';

  _setText('kpi-rows',    rows.toLocaleString());
  _setText('kpi-cols',    cols.toString());
  _setText('kpi-numeric', numeric.toString());
  _setText('kpi-missing', missing.toLocaleString());
  _setText('kpi-dups',    dups.toLocaleString());
  _setText('kpi-mem',     memKb);

  /* dataset name */
  _setText('dash-dataset-name', info.file_name || 'Dataset');
  _setText('dash-badge',        `${rows.toLocaleString()} rows`);
  _setText('preview-meta',      `First ${Math.min(10, rows)} rows`);

  /* column types donut */
  if (info.dtypes) {
    const counts = {};
    Object.values(info.dtypes).forEach(t => { counts[t] = (counts[t] || 0) + 1; });
    charts.pieChart('chart-dtypes', Object.keys(counts), Object.values(counts), '');
  }

  /* missing bar */
  const missingCols = Object.entries(info.missing || {}).filter(([, v]) => v > 0);
  if (missingCols.length) {
    _setText('missing-card-meta', `${missingCols.length} col(s) affected`);
    charts.barChart(
      'chart-missing',
      missingCols.slice(0, 12).map(([k, v]) => ({ x: k, y: v })),
      '', '', 'Missing count'
    );
  } else {
    _setText('missing-card-meta', 'None');
    document.getElementById('chart-missing').innerHTML =
      `<div class="zero-missing"><span>✅</span> No missing values</div>`;
  }

  /* preview table */
  if (info.preview) {
    _renderTableFromRecords('dash-preview-table', info.columns, info.preview);
  }
}

function _setText (id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function clearData () {
  showLoading('Clearing data…');
  try {
    await api.request('/api/data/clear', { method: 'DELETE' });
  } catch (_) {}
  AppState.hasData  = false;
  AppState.columns  = [];
  AppState.numericColumns     = [];
  AppState.categoricalColumns = [];
  AppState.dataInfo = null;
  _updateDataStatus(false, 'No data loaded');
  hideLoading();
  showToast('Dataset cleared', 'info');
  _showHeroEmpty();
}

async function loadSampleDataset (name) {
  showLoading(`Loading ${name} dataset…`);
  try {
    const result = await api.loadSampleDataset(name);
    _applyDataResult(result, `sample: ${name}`);
    showToast(`Loaded ${name} dataset`, 'success');
    await loadDashboard();
  } catch (err) {
    showToast('Failed to load sample: ' + err.message, 'error');
    hideLoading();
  }
}

function _applyDataResult (result, source) {
  AppState.hasData = true;
  AppState.columns = result.columns || [];
  if (result.dtypes) {
    AppState.numericColumns = Object.entries(result.dtypes)
      .filter(([, t]) => ['int64','float64','int32','float32'].some(nt => t.includes(nt)))
      .map(([c]) => c);
    AppState.categoricalColumns = AppState.columns
      .filter(c => !AppState.numericColumns.includes(c));
  }
  _updateDataStatus(true, source || result.file_name || 'Data loaded');
}


/* ═══════════════════════════════════════════════════════════════
   DATA SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadDataSection () {
  /* setup upload zone handlers */
  const zone      = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');
  if (!zone || !fileInput) return;

  zone.onclick = () => fileInput.click();

  fileInput.onchange = e => {
    if (e.target.files.length) {
      uploadFile(e.target.files[0]);
      e.target.value = '';
    }
  };

  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', ()   => zone.classList.remove('dragover'));
  zone.addEventListener('drop',      e  => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
  });

  /* if data already loaded, show preview */
  if (AppState.hasData) {
    const info = await api.getDataInfo().catch(() => null);
    if (info?.preview) {
      const wrap = document.getElementById('data-preview-wrap');
      if (wrap) {
        wrap.classList.remove('hidden');
        _setText('data-preview-title', `Preview — ${info.file_name || 'dataset'} (${info.shape?.[0]?.toLocaleString()} rows)`);
        _renderTableFromRecords('data-preview-table', info.columns, info.preview);
      }
    }
  }
}

async function uploadFile (file) {
  showLoading(`Uploading ${file.name}…`);
  try {
    const result = await api.uploadFile(file);
    _applyDataResult(result, file.name);
    showToast(`Uploaded ${file.name}`, 'success');

    /* show preview */
    const wrap = document.getElementById('data-preview-wrap');
    if (wrap && result.preview) {
      wrap.classList.remove('hidden');
      _setText('data-preview-title', `Preview — ${file.name} (${result.shape?.[0]?.toLocaleString()} rows)`);
      _renderTableFromRecords('data-preview-table', result.columns, result.preview);
    }
  } catch (err) {
    showToast('Upload failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

function exportData (fmt) {
  window.location.href = `/api/data/export/${fmt}`;
}


/* ═══════════════════════════════════════════════════════════════
   EDA SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadEDASection () {
  loadEDATab('profile');
}

async function loadEDATab (tab, el = null) {
  /* update tab active state */
  document.querySelectorAll('#eda-content .itab, #eda-content .inner-tab')
    .forEach(t => t.classList.remove('active'));
  if (el) {
    el.classList.add('active');
  } else {
    document.querySelectorAll('#eda-content .itab, #eda-content .inner-tab').forEach(btn => {
      if (btn.textContent.toLowerCase().includes(tab)) btn.classList.add('active');
    });
  }

  const content = document.getElementById('eda-tab-content');
  if (!content) return;
  content.innerHTML = _spinner();

  try {
    switch (tab) {
      case 'profile': {
        const profile = await api.getProfile();
        content.innerHTML = _renderProfile(profile);
        break;
      }
      case 'distribution': {
        content.innerHTML = `
          <div class="glass-card">
            <div class="card-head"><span class="card-title">Column distribution</span></div>
            <label class="form-label">Select column</label>
            <select class="form-select" id="dist-column" onchange="renderDistribution()">
              ${AppState.columns.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
          </div>
          <div class="glass-card mt-4">
            <div class="chart-wrap" id="dist-chart" style="height:360px;"></div>
          </div>`;
        renderDistribution();
        break;
      }
      case 'correlation': {
        const corr = await api.getCorrelation();
        if (corr) {
          content.innerHTML = `<div class="glass-card">
            <div class="card-head"><span class="card-title">Correlation matrix</span></div>
            <div class="chart-wrap" id="corr-chart" style="height:480px;"></div>
          </div>`;
          charts.renderPlotlyJSON('corr-chart', corr);
        } else {
          content.innerHTML = _emptyState('Not enough numeric columns for correlation analysis.');
        }
        break;
      }
      case 'missing': {
        const profileData = await api.getProfile();
        content.innerHTML = _renderMissingTable(profileData);
        break;
      }
    }
  } catch (err) {
    content.innerHTML = _errorCard(err.message);
  }
}

function _renderProfile (profile) {
  if (profile.error) return _errorCard(profile.error);
  const p = profile.profile || profile;
  const shape = p.shape || [0,0];

  let html = `
    <div class="kpi-strip" style="grid-template-columns:repeat(4,1fr);margin-bottom:20px;">
      <div class="kpi-tile"><span class="kpi-value">${shape[0]?.toLocaleString()}</span><span class="kpi-label">Rows</span></div>
      <div class="kpi-tile"><span class="kpi-value">${shape[1]}</span><span class="kpi-label">Columns</span></div>
      <div class="kpi-tile"><span class="kpi-value">${Object.keys(p.numeric_summary||{}).length}</span><span class="kpi-label">Numeric</span></div>
      <div class="kpi-tile"><span class="kpi-value">${Object.keys(p.categorical_summary||{}).length}</span><span class="kpi-label">Categorical</span></div>
    </div>`;

  /* numeric summary table */
  const numCols = Object.keys(p.numeric_summary || {});
  if (numCols.length) {
    html += `<div class="glass-card mt-4">
      <div class="card-head"><span class="card-title">Numeric summary</span></div>
      <div class="table-scroll"><table class="data-table"><thead><tr>
        <th>Column</th><th>Mean</th><th>Median</th><th>Std</th><th>Min</th><th>Max</th><th>Skewness</th><th>Missing</th>
      </tr></thead><tbody>`;
    numCols.forEach(col => {
      const s = p.numeric_summary[col];
      const missing = p.missing?.[col];
      const missPct = missing ? `${missing.count} (${missing.pct.toFixed(1)}%)` : '0';
      html += `<tr>
        <td>${col}</td>
        <td>${s.mean?.toFixed(3) ?? '—'}</td>
        <td>${s.median?.toFixed(3) ?? '—'}</td>
        <td>${s.std?.toFixed(3) ?? '—'}</td>
        <td>${s.min?.toFixed(3) ?? '—'}</td>
        <td>${s.max?.toFixed(3) ?? '—'}</td>
        <td>${s.skewness?.toFixed(3) ?? '—'}</td>
        <td>${missPct}</td>
      </tr>`;
    });
    html += `</tbody></table></div></div>`;
  }

  /* categorical summary */
  const catCols = Object.keys(p.categorical_summary || {});
  if (catCols.length) {
    html += `<div class="glass-card mt-4">
      <div class="card-head"><span class="card-title">Categorical summary</span></div>
      <div class="table-scroll"><table class="data-table"><thead><tr>
        <th>Column</th><th>Unique</th><th>Top value</th><th>Top %</th>
      </tr></thead><tbody>`;
    catCols.forEach(col => {
      const s = p.categorical_summary[col];
      const topVal = Object.keys(s.top_values||{})[0] || '—';
      html += `<tr>
        <td>${col}</td>
        <td>${s.unique}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${topVal}</td>
        <td>${s.top_pct?.toFixed(1) ?? '—'}%</td>
      </tr>`;
    });
    html += `</tbody></table></div></div>`;
  }

  /* issues */
  const issues = profile.issues || {};
  const issueCount = (issues.missing_high?.length||0) + (issues.missing_medium?.length||0) +
    (issues.constant_columns?.length||0) + (issues.duplicates||0);
  if (issueCount > 0) {
    html += `<div class="glass-card mt-4">
      <div class="card-head">
        <span class="card-title">Data quality issues</span>
        <span class="badge badge-warning">${issueCount} found</span>
      </div>`;
    if (issues.duplicates) html += `<div class="log-row"><span class="log-step">Duplicates</span><span class="log-detail">${issues.duplicates} duplicate rows detected</span></div>`;
    (issues.missing_high||[]).forEach(i => { html += `<div class="log-row"><span class="log-step" style="color:var(--red);">High missing</span><span class="log-detail">${i.column}: ${i.pct.toFixed(1)}% missing</span></div>`; });
    (issues.missing_medium||[]).forEach(i => { html += `<div class="log-row"><span class="log-step" style="color:var(--amber);">Med missing</span><span class="log-detail">${i.column}: ${i.pct.toFixed(1)}% missing</span></div>`; });
    (issues.constant_columns||[]).forEach(c => { html += `<div class="log-row"><span class="log-step" style="color:var(--violet);">Constant</span><span class="log-detail">${c}</span></div>`; });
    html += `</div>`;
  }

  return html;
}

function _renderMissingTable (profile) {
  const p       = profile.profile || profile;
  const missing = p.missing || {};
  const hasMissing = Object.values(missing).some(v => (v.count ?? v) > 0);

  if (!hasMissing) {
    return `<div class="glass-card">
      <div class="zero-missing"><span>✅</span> No missing values detected in any column.</div>
    </div>`;
  }

  let html = `<div class="glass-card">
    <div class="card-head"><span class="card-title">Missing value analysis</span></div>
    <div class="table-scroll"><table class="data-table"><thead><tr>
      <th>Column</th><th>Missing count</th><th>Missing %</th><th>Severity</th>
    </tr></thead><tbody>`;

  Object.entries(missing).forEach(([col, val]) => {
    const count = val.count ?? val;
    const pct   = val.pct   ?? 0;
    if (!count) return;
    const sev   = pct > 50 ? `<span class="badge badge-danger">High</span>` :
                  pct > 10 ? `<span class="badge badge-warning">Medium</span>` :
                              `<span class="badge badge-info">Low</span>`;
    html += `<tr><td>${col}</td><td>${count.toLocaleString()}</td><td>${pct.toFixed(1)}%</td><td>${sev}</td></tr>`;
  });

  html += `</tbody></table></div></div>`;
  return html;
}

async function renderDistribution () {
  const col = document.getElementById('dist-column')?.value;
  if (!col) return;
  try {
    const dist = await api.getDistribution(col);
    if (dist?.data) charts.renderPlotlyJSON('dist-chart', dist);
  } catch (err) {
    console.error('Distribution error:', err);
  }
}


/* ═══════════════════════════════════════════════════════════════
   CLEANING SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadCleaningSection () {
  const recWrap = document.getElementById('cleaning-rec-wrap');
  if (recWrap) recWrap.innerHTML = _spinner();

  try {
    const recs = await api.getCleaningRecommendations();
    if (recWrap) recWrap.innerHTML = _renderRecommendations(recs);
  } catch (err) {
    if (recWrap) recWrap.innerHTML = _errorCard(err.message);
  }
}

function _renderRecommendations (recs) {
  if (!recs) return '';
  let html = '';

  const items = [
    ...(recs.missing    || []).map(r => ({ ...r, type: 'missing' })),
    ...(recs.outliers   || []).map(r => ({ ...r, type: 'outlier' })),
    ...(recs.duplicates || []).map(r => ({ ...r, type: 'duplicate', column: 'All' })),
  ];

  if (!items.length) {
    return `<div class="glass-card">
      <div class="zero-missing"><span>✅</span> No cleaning recommendations. Your data looks clean!</div>
    </div>`;
  }

  const typeBadge = { missing: 'badge-warning', outlier: 'badge-info', duplicate: 'badge-danger' };

  html += `<div class="glass-card">
    <div class="card-head">
      <span class="card-title">Recommendations</span>
      <span class="badge badge-warning">${items.length} item${items.length > 1 ? 's' : ''}</span>
    </div>
    <div class="rec-list">`;

  items.forEach(r => {
    const prio = r.priority === 'high' ? 'badge-danger' : r.priority === 'medium' ? 'badge-warning' : 'badge-info';
    html += `<div class="rec-row">
      <span class="badge ${typeBadge[r.type] || 'badge-info'}">${r.type}</span>
      <span class="rec-col">${r.column || '—'}</span>
      <span class="rec-issue">${r.issue || r.action || '—'}</span>
      <span class="badge ${prio}">${r.priority || '—'}</span>
    </div>`;
  });

  html += `</div></div>`;
  return html;
}

async function handleMissing () {
  showLoading('Handling missing values…');
  try {
    const strategy = document.getElementById('missing-strategy')?.value || 'median';
    const result   = await api.handleMissing(strategy, null);
    showToast(`Missing values handled (${strategy})`, 'success');
    _appendCleaningLog({ step: 'missing_values', strategy, ...result.log });
    await loadCleaningSection();
  } catch (err) {
    showToast('Failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleOutliers () {
  showLoading('Handling outliers…');
  try {
    const method = document.getElementById('outlier-method')?.value || 'clip_iqr';
    const result = await api.handleOutliers(method, null);
    showToast(`Outliers handled (${method})`, 'success');
    _appendCleaningLog({ step: 'outliers', method, ...result.log });
    await loadCleaningSection();
  } catch (err) {
    showToast('Failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleDuplicates () {
  showLoading('Removing duplicates…');
  try {
    const strategy = document.getElementById('dup-strategy')?.value || 'drop_all';
    const result   = await api.request('/api/cleaning/duplicates', {
      method: 'POST', body: JSON.stringify({ strategy })
    });
    showToast(`Duplicates removed: ${result.log?.rows_removed || 0} rows`, 'success');
    _appendCleaningLog({ step: 'duplicates', strategy, ...result.log });
    await loadCleaningSection();
  } catch (err) {
    showToast('Failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function autoClean (aggressive = false) {
  showLoading(aggressive ? 'Running aggressive clean…' : 'Auto-cleaning data…');
  try {
    const result = await api.autoClean(aggressive);
    const steps  = result.logs?.length || 0;
    showToast(`Auto-clean complete: ${steps} step${steps !== 1 ? 's' : ''} applied`, 'success');
    (result.logs || []).forEach(log => _appendCleaningLog(log));
    await loadCleaningSection();
  } catch (err) {
    showToast('Auto-clean failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function undoCleaning () {
  showLoading('Undoing last step…');
  try {
    const result = await api.request('/api/cleaning/undo', { method: 'POST' });
    if (result.success) {
      showToast('Undo successful', 'success');
      await loadCleaningSection();
    } else {
      showToast('Nothing to undo', 'warning');
    }
  } catch (err) {
    showToast('Undo failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

function _appendCleaningLog (entry) {
  const wrap  = document.getElementById('cleaning-log-wrap');
  const list  = document.getElementById('cleaning-log-list');
  const meta  = document.getElementById('cleaning-log-meta');
  if (!wrap || !list) return;
  wrap.classList.remove('hidden');

  const detail = JSON.stringify(entry, null, 0)
    .replace(/[{}"]/g, '')
    .replace(/,/g, ' · ')
    .replace(/:/g, ': ');

  const row = document.createElement('div');
  row.className = 'log-row';
  row.innerHTML = `<span class="log-step">${entry.step || 'step'}</span>
                   <span class="log-detail">${detail}</span>`;
  list.appendChild(row);

  if (meta) {
    const count = list.querySelectorAll('.log-row').length;
    meta.textContent = `${count} step${count !== 1 ? 's' : ''} applied`;
  }
}


/* ═══════════════════════════════════════════════════════════════
   VISUALIZATION SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadVisualizationSection () {
  /* populate column selects */
  ['viz-x', 'viz-y', 'viz-color'].forEach((id, i) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const opts = i === 2
      ? '<option value="">None</option>' + AppState.columns.map(c => `<option>${c}</option>`).join('')
      : AppState.columns.map(c => `<option>${c}</option>`).join('');
    sel.innerHTML = opts;
  });
}

function selectChartType (type, btn) {
  AppState.selectedChartType = type;
  document.querySelectorAll('.chart-type-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

async function createVisualization () {
  const chartType = AppState.selectedChartType || 'bar';
  const x         = document.getElementById('viz-x')?.value;
  const y         = document.getElementById('viz-y')?.value;
  const color     = document.getElementById('viz-color')?.value || undefined;
  const title     = document.getElementById('viz-title')?.value || '';

  if (!x || !y) { showToast('Select X and Y columns', 'warning'); return; }

  showLoading('Generating chart…');

  const placeholder = document.getElementById('viz-placeholder');
  const chartWrap   = document.getElementById('viz-chart');
  if (placeholder) placeholder.classList.add('hidden');
  if (chartWrap)   chartWrap.classList.remove('hidden');

  try {
    const result = await api.createChart(chartType, { x, y, color, title });
    if (result) charts.renderPlotlyJSON('viz-chart', result);
  } catch (err) {
    showToast('Chart error: ' + err.message, 'error');
    if (placeholder) placeholder.classList.remove('hidden');
    if (chartWrap)   chartWrap.classList.add('hidden');
  } finally {
    hideLoading();
  }
}


/* ═══════════════════════════════════════════════════════════════
   ANALYSIS SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadAnalysisSection () {
  loadAnalysisTab('summary');
}

async function loadAnalysisTab (tab, el = null) {
  document.querySelectorAll('#analysis-content .itab, #analysis-content .inner-tab')
    .forEach(t => t.classList.remove('active'));
  if (el) {
    el.classList.add('active');
  } else {
    document.querySelectorAll('#analysis-content .itab, #analysis-content .inner-tab').forEach(btn => {
      if (btn.textContent.toLowerCase().includes(tab)) btn.classList.add('active');
    });
  }

  const content = document.getElementById('analysis-tab-content');
  if (!content) return;
  content.innerHTML = _spinner();

  const colOpts = AppState.columns.map(c => `<option>${c}</option>`).join('');

  try {
    switch (tab) {
      case 'summary': {
        const stats = await api.getSummaryStats();
        if (!stats || !Object.keys(stats).length) {
          content.innerHTML = _emptyState('No numeric columns to summarise.');
          break;
        }
        let html = `<div class="glass-card">
          <div class="card-head"><span class="card-title">Summary statistics</span></div>
          <div class="table-scroll"><table class="data-table"><thead><tr>
            <th>Column</th><th>Mean</th><th>Std</th><th>Min</th><th>Max</th><th>Missing</th><th>Skewness</th>
          </tr></thead><tbody>`;
        Object.entries(stats).forEach(([col, s]) => {
          html += `<tr>
            <td>${col}</td>
            <td>${s.mean?.toFixed(3) ?? '—'}</td>
            <td>${s.std?.toFixed(3) ?? '—'}</td>
            <td>${s.min?.toFixed(3) ?? '—'}</td>
            <td>${s.max?.toFixed(3) ?? '—'}</td>
            <td>${s.missing ?? 0}</td>
            <td>${s.skewness?.toFixed(3) ?? '—'}</td>
          </tr>`;
        });
        html += `</tbody></table></div></div>`;
        content.innerHTML = html;
        break;
      }

      case 'hypothesis': {
        content.innerHTML = `
          <div class="glass-card">
            <div class="card-head"><span class="card-title">Hypothesis testing</span></div>
            <div class="grid-3">
              <div>
                <label class="form-label">Test type</label>
                <select class="form-select" id="hyp-test">
                  <option value="t_test">Independent t-test</option>
                  <option value="anova">One-way ANOVA</option>
                  <option value="chi_square">Chi-square</option>
                </select>
              </div>
              <div>
                <label class="form-label">Column 1</label>
                <select class="form-select" id="hyp-col1">${colOpts}</select>
              </div>
              <div>
                <label class="form-label">Group / Column 2 (optional)</label>
                <select class="form-select" id="hyp-col2">
                  <option value="">None</option>${colOpts}
                </select>
              </div>
            </div>
            <button class="btn btn-primary mt-3" onclick="runHypothesisTest()">
              <i class="fa-solid fa-flask"></i> Run test
            </button>
            <div id="hyp-result" class="mt-4"></div>
          </div>`;
        break;
      }

      case 'regression': {
        content.innerHTML = `
          <div class="glass-card">
            <div class="card-head"><span class="card-title">Regression analysis</span></div>
            <div class="grid-2">
              <div>
                <label class="form-label">Dependent variable (Y)</label>
                <select class="form-select" id="reg-y">${colOpts}</select>
              </div>
              <div>
                <label class="form-label">Independent variables (X) — multi-select</label>
                <select class="form-select" id="reg-x" multiple style="height:110px;">${colOpts}</select>
              </div>
            </div>
            <button class="btn btn-primary mt-3" onclick="runRegression()">
              <i class="fa-solid fa-chart-line"></i> Run regression
            </button>
            <div id="reg-result" class="mt-4"></div>
          </div>`;
        break;
      }

      case 'anova': {
        content.innerHTML = `
          <div class="glass-card">
            <div class="card-head"><span class="card-title">One-way ANOVA</span></div>
            <div class="grid-2">
              <div>
                <label class="form-label">Group column (categorical)</label>
                <select class="form-select" id="anova-group">${colOpts}</select>
              </div>
              <div>
                <label class="form-label">Value column (numeric)</label>
                <select class="form-select" id="anova-val">${colOpts}</select>
              </div>
            </div>
            <button class="btn btn-primary mt-3" onclick="runANOVA()">
              <i class="fa-solid fa-flask"></i> Run ANOVA
            </button>
            <div id="anova-result" class="mt-4"></div>
          </div>`;
        break;
      }
    }
  } catch (err) {
    content.innerHTML = _errorCard(err.message);
  }
}

async function runHypothesisTest () {
  showLoading('Running hypothesis test…');
  try {
    const testType = document.getElementById('hyp-test').value;
    const col1     = document.getElementById('hyp-col1').value;
    const col2     = document.getElementById('hyp-col2').value || undefined;
    const result   = await api.hypothesisTest(testType, { column1: col1, group_column: col2 });
    document.getElementById('hyp-result').innerHTML = _renderStatResult(result);
  } catch (err) {
    showToast('Test failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runRegression () {
  showLoading('Running regression…');
  try {
    const dep   = document.getElementById('reg-y').value;
    const indep = Array.from(document.getElementById('reg-x').selectedOptions).map(o => o.value);
    if (!indep.length) { showToast('Select at least one independent variable', 'warning'); return; }
    const result = await api.regressionAnalysis(dep, indep);
    document.getElementById('reg-result').innerHTML = _renderStatResult(result);
  } catch (err) {
    showToast('Regression failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runANOVA () {
  showLoading('Running ANOVA…');
  try {
    const group = document.getElementById('anova-group').value;
    const val   = document.getElementById('anova-val').value;
    const result = await api.request('/api/analysis/anova', {
      method: 'POST', body: JSON.stringify({ group_column: group, value_column: val })
    });
    document.getElementById('anova-result').innerHTML = _renderStatResult(result);
  } catch (err) {
    showToast('ANOVA failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}

function _renderStatResult (result) {
  if (result.error) return _errorCard(result.error);
  const sig   = result.significant;
  const pval  = result.p_value ?? result.f_pvalue;
  const badge = sig
    ? `<span class="badge badge-success">Significant (p < 0.05)</span>`
    : `<span class="badge badge-warning">Not significant (p ≥ 0.05)</span>`;

  let html = `<div class="glass-card">
    <div class="card-head">
      <span class="card-title">${result.test || 'Result'}</span>
      ${sig !== undefined ? badge : ''}
    </div>`;

  const rows = Object.entries(result).filter(([k]) =>
    !['test', 'significant', 'interpretation', 'summary', 'classification_report', 'confusion_matrix', 'coefficients', 'p_values'].includes(k)
  );

  html += `<div class="table-scroll"><table class="data-table"><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>`;
  rows.forEach(([k, v]) => {
    const display = typeof v === 'number' ? v.toFixed(5) : String(v);
    html += `<tr><td>${k}</td><td>${display}</td></tr>`;
  });
  html += `</tbody></table></div>`;

  if (result.interpretation) {
    html += `<p style="margin-top:12px;color:var(--text-2);font-size:0.85rem;">
      <i class="fa-solid fa-lightbulb" style="color:var(--amber);margin-right:6px;"></i>
      ${result.interpretation}
    </p>`;
  }

  /* regression extras */
  if (result.coefficients) {
    html += `<div class="card-head" style="margin-top:16px;"><span class="card-title">Coefficients</span></div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Variable</th><th>Coeff</th><th>p-value</th></tr></thead><tbody>`;
    Object.entries(result.coefficients).forEach(([k, v]) => {
      const pv = result.p_values?.[k];
      const sig = pv !== undefined && pv < 0.05;
      html += `<tr>
        <td>${k}</td>
        <td>${v.toFixed(5)}</td>
        <td>${pv !== undefined ? pv.toFixed(5) : '—'} ${sig ? '<span class="badge badge-success" style="padding:1px 5px;">*</span>' : ''}</td>
      </tr>`;
    });
    html += `</tbody></table></div>`;
  }

  html += `</div>`;
  return html;
}


/* ═══════════════════════════════════════════════════════════════
   MODELING SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadModelingSection () {
  const colOpts = AppState.columns.map(c => `<option>${c}</option>`).join('');
  const tgt     = document.getElementById('ml-target');
  const clust   = document.getElementById('cluster-features');
  if (tgt)  tgt.innerHTML  = colOpts;
  if (clust) clust.innerHTML = colOpts;
}

async function trainModels () {
  const target  = document.getElementById('ml-target')?.value;
  const problem = document.getElementById('ml-problem')?.value || undefined;
  if (!target) { showToast('Select a target column', 'warning'); return; }

  const btn = document.getElementById('train-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Training…'; }

  showLoading('Training models — this may take a moment…');
  try {
    const result = await api.trainModels(target, problem);

    /* show results panel */
    document.getElementById('ml-placeholder')?.classList.add('hidden');
    const wrap = document.getElementById('ml-results-wrap');
    if (wrap) wrap.classList.remove('hidden');

    /* best model banner */
    const banner = document.getElementById('best-model-banner');
    if (banner && result.best_model) {
      const metrics = result.best_metrics || {};
      const scoreKey = Object.keys(metrics)[0] || '';
      const score    = metrics[scoreKey]?.toFixed(4) ?? '';
      banner.innerHTML = `
        <div class="best-model-badge">
          <i class="fa-solid fa-trophy" style="color:var(--amber);"></i>
          <span class="best-model-label">Best model</span>
          <span class="best-model-name">${result.best_model}</span>
          ${score ? `<span class="badge badge-mint">${scoreKey}: ${score}</span>` : ''}
        </div>`;
    }

    /* comparison chart */
    if (result.models) {
      const names   = Object.keys(result.models);
      const metrics = names.map(n => result.models[n].metrics || {});
      charts.modelComparison('ml-chart', names, metrics, '');
    }

    showToast(`Training complete! Best: ${result.best_model}`, 'success');
  } catch (err) {
    showToast('Training failed: ' + err.message, 'error');
  } finally {
    hideLoading();
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-rocket"></i> Train all models'; }
  }
}

async function performClustering () {
  const features = Array.from(document.getElementById('cluster-features')?.selectedOptions || []).map(o => o.value);
  const algo     = document.getElementById('cluster-algo')?.value || 'K-Means';
  const k        = parseInt(document.getElementById('cluster-k')?.value) || 3;

  if (!features.length) { showToast('Select at least one feature', 'warning'); return; }

  showLoading('Clustering…');
  try {
    const result = await api.performClustering(features, algo, k);

    const chartEl = document.getElementById('cluster-chart');
    if (chartEl) {
      chartEl.classList.remove('hidden');
      /* render PCA scatter */
      const pca = result.pca_data || [];
      const labels = result.labels || [];
      const xData  = pca.map(p => p[0]);
      const yData  = pca.map(p => p[1]);
      const colorArr = labels.map(l => charts.colors[l % charts.colors.length]);
      charts.scatterPlot('cluster-chart', xData, yData, '', 'PC1', 'PC2', colorArr);
    }

    showToast(`Clustering done: ${result.n_clusters} clusters${result.silhouette_score !== null ? ` · silhouette ${result.silhouette_score.toFixed(3)}` : ''}`, 'success');
  } catch (err) {
    showToast('Clustering failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}


/* ═══════════════════════════════════════════════════════════════
   MLOPS SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadMLOps () {
  const tableEl = document.getElementById('mlops-table');
  if (tableEl) tableEl.innerHTML = _spinner();

  try {
    const leaderboard = await api.getLeaderboard();
    if (!leaderboard || !leaderboard.length) {
      if (tableEl) tableEl.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-trophy" style="font-size:2rem;color:var(--border-default);"></i>
          <h3>No experiments yet</h3>
          <p>Train models to populate the leaderboard</p>
        </div>`;
      return;
    }

    let html = `<table class="data-table"><thead><tr>
      <th>#</th><th>Model</th><th>Experiment</th><th>Metrics</th><th>Date</th>
    </tr></thead><tbody>`;

    leaderboard.forEach((r, i) => {
      const metricsStr = Object.entries(r.metrics || {})
        .slice(0, 3)
        .map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(4) : v}`)
        .join(' · ');
      html += `<tr>
        <td>${i + 1}</td>
        <td style="font-weight:700;">${r.model || '—'}</td>
        <td>${r.experiment || '—'}</td>
        <td style="font-family:var(--font-mono);font-size:0.7rem;color:var(--mint);">${metricsStr || '—'}</td>
        <td style="color:var(--text-3);">${r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
      </tr>`;
    });
    html += `</tbody></table>`;
    if (tableEl) tableEl.innerHTML = html;
  } catch (err) {
    if (tableEl) tableEl.innerHTML = _errorCard(err.message);
  }
}

/* alias used by section router */
async function loadMLOpsSection () { return loadMLOps(); }


/* ═══════════════════════════════════════════════════════════════
   REPORTS SECTION
   ═══════════════════════════════════════════════════════════════ */
async function loadReportsSection () {
  /* Section HTML is static (defined in HTML), nothing to init dynamically */
}

async function generateReport (format) {
  showLoading(`Generating ${format.toUpperCase()} report…`);
  try {
    const title       = document.getElementById('report-title')?.value || 'FINESE2 Report';
    const include_eda = document.getElementById('r-eda')?.checked ?? true;
    const include_viz = document.getElementById('r-viz')?.checked ?? true;
    const include_ml  = document.getElementById('r-ml')?.checked  ?? false;

    const result = await api.generateReport(format, title, {
      include_eda, include_visualizations: include_viz, include_modeling: include_ml
    });

    /* direct downloads */
    if (format === 'excel') {
      window.location.href = '/api/reports/generate/excel';
      hideLoading();
      return;
    }

    if (result?.success) {
      const dlUrl = `/api/reports/download/${format}`;
      const resultEl = document.getElementById('report-result');
      if (resultEl) {
        resultEl.innerHTML = `
          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--green-dim);
               border:1px solid rgba(63,185,80,0.3);border-radius:var(--r-sm);">
            <i class="fa-solid fa-circle-check" style="color:var(--green);font-size:1.2rem;"></i>
            <span style="color:var(--text-1);font-weight:600;">Report generated successfully</span>
            <a href="${dlUrl}" class="btn btn-sm btn-primary" download>
              <i class="fa-solid fa-download"></i> Download
            </a>
          </div>`;
      }
      showToast('Report ready!', 'success');
    }
  } catch (err) {
    showToast('Report failed: ' + err.message, 'error');
  } finally {
    hideLoading();
  }
}


/* ═══════════════════════════════════════════════════════════════
   TABLE RENDERER
   ═══════════════════════════════════════════════════════════════ */
function _renderTableFromRecords (containerId, columns, rows) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!columns?.length || !rows?.length) {
    container.innerHTML = '<p style="color:var(--text-3);padding:16px;">No data to display.</p>';
    return;
  }

  let html = `<table class="data-table"><thead><tr>`;
  columns.forEach(c => { html += `<th>${c}</th>`; });
  html += `</tr></thead><tbody>`;

  rows.forEach(row => {
    html += '<tr>';
    columns.forEach(c => {
      const val = row[c] ?? '';
      html += `<td title="${String(val)}">${String(val)}</td>`;
    });
    html += '</tr>';
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}


/* ═══════════════════════════════════════════════════════════════
   UI HELPERS
   ═══════════════════════════════════════════════════════════════ */
function _spinner () {
  return `<div style="display:flex;align-items:center;justify-content:center;padding:48px;">
    <div class="spinner"></div>
  </div>`;
}

function _errorCard (msg) {
  return `<div class="glass-card">
    <p style="color:var(--red);font-size:0.9rem;display:flex;align-items:center;gap:8px;">
      <i class="fa-solid fa-circle-exclamation"></i> ${msg}
    </p>
  </div>`;
}

function _emptyState (msg) {
  return `<div class="glass-card">
    <div class="empty-state">
      <i class="fa-solid fa-inbox empty-icon"></i>
      <p>${msg}</p>
    </div>
  </div>`;
}


/* ═══════════════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {

  /* hide loading veil after page is ready */
  setTimeout(() => hideLoading(), 600);

  /* nav item click delegation (for any dynamically generated items) */
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const section = item.dataset.section;
      if (section) navigateTo(section, item);
    });
  });

  /* check if server already has data (page reload) */
  api.getStatus().then(status => {
    if (status.data_loaded) {
      AppState.hasData = true;
      _updateDataStatus(true, status.file_name || 'Data loaded');
      api.getDataInfo().then(info => {
        if (info?.columns) {
          AppState.columns = info.columns;
          if (info.dtypes) {
            AppState.numericColumns = Object.entries(info.dtypes)
              .filter(([, t]) => ['int64','float64','int32','float32'].some(nt => t.includes(nt)))
              .map(([c]) => c);
            AppState.categoricalColumns = AppState.columns
              .filter(c => !AppState.numericColumns.includes(c));
          }
        }
      }).catch(() => {});
    }
  }).catch(() => {});

  /* load initial section */
  loadDashboard();
});