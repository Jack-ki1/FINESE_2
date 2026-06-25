
content = """# FINESE_2 Enhancement Guide

## Comprehensive Improvements: Features, MLOps & Modern Light UI

---

## Table of Contents
1. [Design Philosophy](#1-design-philosophy)
2. [Global UI/UX Overhaul](#2-global-uiux-overhaul)
3. [Review Enhancements](#3-review-enhancements)
4. [Cleaning Enhancements](#4-cleaning-enhancements)
5. [Charts & Pivot Enhancements](#5-charts--pivot-enhancements)
6. [Chatbot Production Integration](#6-chatbot-production-integration)
7. [SQL Enhancements](#7-sql-enhancements)
8. [Export Diversification](#8-export-diversification)
9. [New: MLOps Module](#9-new-mlops-module)
10. [Running the Enhanced Dashboard](#10-running-the-enhanced-dashboard)

---

## 1. Design Philosophy

### Light Theme Only — "FINESE Light Pro"

Inspired by modern SaaS dashboards (Notion, Linear, Vercel, Supabase):
- **Clean, airy interfaces** with generous whitespace
- **Subtle depth** through layered surfaces rather than heavy shadows
- **Color as information** — data colors are vibrant, UI chrome is neutral
- **Motion with purpose** — every animation guides attention

### Color Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary: #F1F5F9;
  --bg-elevated: #FFFFFF;
  
  /* Surfaces */
  --surface-default: #FFFFFF;
  --surface-hover: #F8FAFC;
  --surface-active: #F1F5F9;
  --surface-selected: #EEF2FF;
  
  /* Borders */
  --border-subtle: #E2E8F0;
  --border-default: #CBD5E1;
  --border-strong: #94A3B8;
  
  /* Text */
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-tertiary: #94A3B8;
  --text-inverse: #FFFFFF;
  
  /* Brand / Primary */
  --primary-50: #EEF2FF;
  --primary-100: #E0E7FF;
  --primary-200: #C7D2FE;
  --primary-300: #A5B4FC;
  --primary-400: #818CF8;
  --primary-500: #6366F1;
  --primary-600: #4F46E5;
  --primary-700: #4338CA;
  
  /* Semantic */
  --success-50: #F0FDF4;
  --success-500: #22C55E;
  --success-600: #16A34A;
  --warning-50: #FFFBEB;
  --warning-500: #EAB308;
  --warning-600: #CA8A04;
  --danger-50: #FEF2F2;
  --danger-500: #EF4444;
  --danger-600: #DC2626;
  
  /* Data Visualization */
  --data-blue: #3B82F6;
  --data-indigo: #6366F1;
  --data-violet: #8B5CF6;
  --data-pink: #EC4899;
  --data-rose: #F43F5E;
  --data-orange: #F97316;
  --data-amber: #F59E0B;
  --data-emerald: #10B981;
  --data-cyan: #06B6D4;
  
  /* Shadows */
  --shadow-xs: 0 1px 2px 0 rgb(15 23 42 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(15 23 42 / 0.08), 0 1px 2px -1px rgb(15 23 42 / 0.08);
  --shadow-md: 0 4px 6px -1px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.08);
  --shadow-lg: 0 10px 15px -3px rgb(15 23 42 / 0.08), 0 4px 6px -4px rgb(15 23 42 / 0.08);
  --shadow-xl: 0 20px 25px -5px rgb(15 23 42 / 0.08), 0 8px 10px -6px rgb(15 23 42 / 0.08);
  
  /* Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-full: 9999px;
}
```

### Typography
- **Primary**: Inter, system-ui, -apple-system, sans-serif
- **Mono**: JetBrains Mono, 'Fira Code', monospace
- **Scale**: 12px (caption), 14px (body), 16px (lead), 20px (h4), 24px (h3), 30px (h2), 36px (h1)

### Spacing System (4px base)
- xs: 4px | sm: 8px | md: 12px | lg: 16px | xl: 24px | 2xl: 32px | 3xl: 48px

---

## 2. Global UI/UX Overhaul

### 2.1 New Dependencies

Update `requirements.txt`:

```txt
flask>=3.0
flask-session>=0.8
pandas>=2.0
numpy>=1.24
plotly>=5.18
duckdb>=0.9
scikit-learn>=1.3
xgboost>=2.0
lightgbm>=4.0
catboost>=1.2
openai>=1.0
google-generativeai>=0.3
reportlab>=4.0
python-pptx>=0.6
python-dotenv>=1.0
nbformat>=5.9
pyarrow>=14.0
weasyprint>=60.0
cryptography>=41.0
```

### 2.2 Modified: `app.py`

```python
import os
from flask import Flask, render_template, session
from flask_session import Session
from datetime import timedelta
import state
from core.dataset_store import DatasetStore
from routes import (
    data_bp, review_bp, cleaning_bp, charts_bp, 
    chatbot_bp, ml_bp, sql_bp, export_bp, mlops_bp
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

Session(app)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/exports', exist_ok=True)
os.makedirs('static/reports', exist_ok=True)

app.dataset_store = DatasetStore(base_path='static/uploads')

app.register_blueprint(data_bp)
app.register_blueprint(review_bp, url_prefix='/review')
app.register_blueprint(cleaning_bp, url_prefix='/cleaning')
app.register_blueprint(charts_bp, url_prefix='/charts')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(ml_bp, url_prefix='/ml')
app.register_blueprint(sql_bp, url_prefix='/sql')
app.register_blueprint(export_bp, url_prefix='/export')
app.register_blueprint(mlops_bp, url_prefix='/mlops')

@app.before_request
def init_session():
    if 'initialized' not in session:
        for key, val in state.DEFAULT_STATE.items():
            session[key] = val
        session['initialized'] = True
        session.permanent = True

@app.route('/')
def index():
    return render_template('review.html', active_tab='review')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 2.3 Modified: `routes/__init__.py`

```python
from .data import bp as data_bp
from .review import bp as review_bp
from .cleaning import bp as cleaning_bp
from .charts import bp as charts_bp
from .chatbot import bp as chatbot_bp
from .ml import bp as ml_bp
from .sql import bp as sql_bp
from .export import bp as export_bp
from .mlops import bp as mlops_bp
```

### 2.4 New: `templates/base.html` — Modern Light Master Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FINESE 2 — Smart Data Explorer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/styles/ag-grid.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/styles/ag-theme-alpine.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
    <div class="app-layout">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-brand">
                <div class="brand-icon">
                    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                        <rect width="28" height="28" rx="8" fill="#6366F1"/>
                        <path d="M8 20L12 12L16 16L20 8" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <span class="brand-text">FINESE</span>
            </div>
            
            <div class="sidebar-section">
                <span class="sidebar-label">Data Source</span>
                <div class="upload-zone" id="uploadZone">
                    <input type="file" id="fileInput" accept=".csv,.xlsx,.xls,.json" hidden>
                    <div class="upload-content">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17 8 12 3 7 8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                        <span class="upload-text">Drop file or click</span>
                        <span class="upload-hint">CSV, Excel, JSON up to 50MB</span>
                    </div>
                </div>
                <div class="upload-status" id="uploadStatus"></div>
            </div>
            
            <div class="sidebar-section">
                <span class="sidebar-label">Dataset</span>
                <div class="dataset-card" id="datasetCard">
                    <div class="dataset-empty">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <ellipse cx="12" cy="5" rx="9" ry="3"/>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                        </svg>
                        <span>No dataset loaded</span>
                    </div>
                </div>
            </div>
            
            <div class="sidebar-section">
                <span class="sidebar-label">Shape</span>
                <div class="shape-control">
                    <label>Row limit</label>
                    <input type="number" id="rowLimit" value="0" min="0" placeholder="∞">
                </div>
            </div>
        </aside>
        
        <!-- Main Content -->
        <main class="main">
            <!-- Top Bar -->
            <header class="topbar">
                <div class="topbar-left">
                    <h1 class="page-title" id="pageTitle">Review</h1>
                    <span class="dataset-badge" id="datasetBadge" style="display:none;"></span>
                </div>
                <div class="topbar-right">
                    <button class="btn-icon" title="Help">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                    </button>
                </div>
            </header>
            
            <!-- Navigation Tabs -->
            <nav class="tab-bar">
                <a class="tab-item {% if active_tab == 'review' %}active{% endif %}" href="{{ url_for('review.review_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                    Review
                </a>
                <a class="tab-item {% if active_tab == 'cleaning' %}active{% endif %}" href="{{ url_for('cleaning.cleaning_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                    Cleaning
                </a>
                <a class="tab-item {% if active_tab == 'charts' %}active{% endif %}" href="{{ url_for('charts.charts_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="20" x2="18" y2="10"/>
                        <line x1="12" y1="20" x2="12" y2="4"/>
                        <line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                    Charts
                </a>
                <a class="tab-item {% if active_tab == 'chatbot' %}active{% endif %}" href="{{ url_for('chatbot.chatbot_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    Chatbot
                </a>
                <a class="tab-item {% if active_tab == 'ml' %}active{% endif %}" href="{{ url_for('ml.ml_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2a10 10 0 1 0 10 10H12V2z"/>
                        <path d="M12 2a10 10 0 0 1 10 10"/>
                        <path d="M12 12L2.5 8.5"/>
                    </svg>
                    ML Studio
                </a>
                <a class="tab-item {% if active_tab == 'sql' %}active{% endif %}" href="{{ url_for('sql.sql_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                    SQL
                </a>
                <a class="tab-item {% if active_tab == 'mlops' %}active{% endif %}" href="{{ url_for('mlops.mlops_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                    MLOps
                </a>
                <a class="tab-item {% if active_tab == 'export' %}active{% endif %}" href="{{ url_for('export.export_page') }}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Export
                </a>
            </nav>
            
            <!-- Page Content -->
            <div class="content">
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 2.5 New: `static/css/style.css` — Complete Modern Light Theme

```css
/* ============================================
   FINESE 2 — Modern Light Theme
   ============================================ */

:root {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary: #F1F5F9;
  --bg-elevated: #FFFFFF;
  --surface-default: #FFFFFF;
  --surface-hover: #F8FAFC;
  --surface-active: #F1F5F9;
  --surface-selected: #EEF2FF;
  --border-subtle: #E2E8F0;
  --border-default: #CBD5E1;
  --border-strong: #94A3B8;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-tertiary: #94A3B8;
  --text-inverse: #FFFFFF;
  --primary-50: #EEF2FF;
  --primary-100: #E0E7FF;
  --primary-200: #C7D2FE;
  --primary-300: #A5B4FC;
  --primary-400: #818CF8;
  --primary-500: #6366F1;
  --primary-600: #4F46E5;
  --primary-700: #4338CA;
  --success-50: #F0FDF4;
  --success-500: #22C55E;
  --success-600: #16A34A;
  --warning-50: #FFFBEB;
  --warning-500: #EAB308;
  --warning-600: #CA8A04;
  --danger-50: #FEF2F2;
  --danger-500: #EF4444;
  --danger-600: #DC2626;
  --data-blue: #3B82F6;
  --data-indigo: #6366F1;
  --data-violet: #8B5CF6;
  --data-pink: #EC4899;
  --data-rose: #F43F5E;
  --data-orange: #F97316;
  --data-amber: #F59E0B;
  --data-emerald: #10B981;
  --data-cyan: #06B6D4;
  --shadow-xs: 0 1px 2px 0 rgb(15 23 42 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(15 23 42 / 0.08), 0 1px 2px -1px rgb(15 23 42 / 0.08);
  --shadow-md: 0 4px 6px -1px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.08);
  --shadow-lg: 0 10px 15px -3px rgb(15 23 42 / 0.08), 0 4px 6px -4px rgb(15 23 42 / 0.08);
  --shadow-xl: 0 20px 25px -5px rgb(15 23 42 / 0.08), 0 8px 10px -6px rgb(15 23 42 / 0.08);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-full: 9999px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg-secondary);
  color: var(--text-primary);
  line-height: 1.5;
  overflow: hidden;
}

/* ============================================
   Layout
   ============================================ */

.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

/* ============================================
   Sidebar
   ============================================ */

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.sidebar-section {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.sidebar-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed var(--border-default);
  border-radius: var(--radius-lg);
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-secondary);
}

.upload-zone:hover {
  border-color: var(--primary-500);
  background: var(--primary-50);
}

.upload-zone.dragover {
  border-color: var(--primary-500);
  background: var(--primary-50);
  transform: scale(1.02);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
}

.upload-content svg {
  color: var(--text-tertiary);
}

.upload-text {
  font-size: 13px;
  font-weight: 500;
}

.upload-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.upload-status {
  margin-top: 8px;
  font-size: 12px;
  min-height: 18px;
}

.upload-status.success { color: var(--success-600); }
.upload-status.error { color: var(--danger-600); }

/* Dataset Card */
.dataset-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.dataset-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.dataset-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dataset-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dataset-meta {
  font-size: 11px;
  color: var(--text-tertiary);
}

.dataset-shape {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.shape-badge {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* Shape Control */
.shape-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shape-control label {
  font-size: 12px;
  color: var(--text-secondary);
}

.shape-control input {
  padding: 8px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: inherit;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.shape-control input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

/* ============================================
   Top Bar
   ============================================ */

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.dataset-badge {
  background: var(--primary-50);
  color: var(--primary-700);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

/* ============================================
   Tab Bar
   ============================================ */

.tab-bar {
  display: flex;
  gap: 4px;
  padding: 0 32px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  overflow-x: auto;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  white-space: nowrap;
  transition: all 0.2s;
  position: relative;
}

.tab-item:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.tab-item.active {
  color: var(--primary-600);
  border-bottom-color: var(--primary-500);
  font-weight: 600;
}

.tab-item svg {
  flex-shrink: 0;
}

/* ============================================
   Cards & Surfaces
   ============================================ */

.card {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
  font-weight: 600;
  font-size: 14px;
}

.card-body {
  padding: 20px;
}

.card-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-secondary);
}

/* Metric Cards */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary-500);
  opacity: 0;
  transition: opacity 0.2s;
}

.metric-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.metric-card:hover::before {
  opacity: 1;
}

.metric-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.metric-delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.metric-delta.positive {
  background: var(--success-50);
  color: var(--success-600);
}

.metric-delta.negative {
  background: var(--danger-50);
  color: var(--danger-600);
}

/* ============================================
   Buttons
   ============================================ */

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-500);
  color: var(--text-inverse);
  border-color: var(--primary-500);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-600);
  border-color: var(--primary-600);
  box-shadow: 0 4px 12px rgb(99 102 241 / 0.3);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-color: var(--border-default);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-tertiary);
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.btn-success {
  background: var(--success-500);
  color: var(--text-inverse);
  border-color: var(--success-500);
}

.btn-success:hover:not(:disabled) {
  background: var(--success-600);
  border-color: var(--success-600);
}

.btn-danger {
  background: var(--danger-500);
  color: var(--text-inverse);
  border-color: var(--danger-500);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: transparent;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-lg {
  padding: 12px 24px;
  font-size: 14px;
}

/* ============================================
   Forms
   ============================================ */

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-control {
  padding: 10px 14px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: inherit;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
  width: 100%;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.form-control::placeholder {
  color: var(--text-tertiary);
}

textarea.form-control {
  resize: vertical;
  min-height: 80px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
}

select.form-control {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
}

/* ============================================
   Tables
   ============================================ */

.table-container {
  overflow-x: auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table thead {
  background: var(--bg-secondary);
}

.table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}

.table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-secondary);
}

.table tbody tr:hover {
  background: var(--bg-secondary);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

/* ============================================
   Badges
   ============================================ */

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
}

.badge-primary { background: var(--primary-50); color: var(--primary-700); }
.badge-success { background: var(--success-50); color: var(--success-600); }
.badge-warning { background: var(--warning-50); color: var(--warning-600); }
.badge-danger { background: var(--danger-50); color: var(--danger-600); }
.badge-secondary { background: var(--bg-tertiary); color: var(--text-secondary); }

/* ============================================
   Alerts
   ============================================ */

.alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  font-size: 13px;
  margin-bottom: 20px;
}

.alert-info {
  background: var(--primary-50);
  border: 1px solid var(--primary-200);
  color: var(--primary-700);
}

.alert-success {
  background: var(--success-50);
  border: 1px solid rgb(34 197 94 / 0.2);
  color: var(--success-600);
}

.alert-warning {
  background: var(--warning-50);
  border: 1px solid rgb(234 179 8 / 0.2);
  color: var(--warning-600);
}

.alert-danger {
  background: var(--danger-50);
  border: 1px solid rgb(239 68 68 / 0.2);
  color: var(--danger-600);
}

/* ============================================
   Progress
   ============================================ */

.progress {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), var(--primary-400));
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

/* ============================================
   Empty States
   ============================================ */

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--text-tertiary);
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 13px;
  max-width: 320px;
}

/* ============================================
   Toast Notifications
   ============================================ */

.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  font-size: 13px;
  min-width: 300px;
  animation: toastSlide 0.3s ease;
  pointer-events: all;
}

.toast-success { border-left: 3px solid var(--success-500); }
.toast-error { border-left: 3px solid var(--danger-500); }
.toast-warning { border-left: 3px solid var(--warning-500); }

@keyframes toastSlide {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* ============================================
   Chat Interface
   ============================================ */

.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 400px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.chat-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
}

.chat-avatar.user {
  background: var(--primary-500);
  color: white;
}

.chat-avatar.assistant {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.chat-bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: 13px;
  line-height: 1.6;
}

.chat-message.user .chat-bubble {
  background: var(--primary-500);
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant .chat-bubble {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  border-bottom-left-radius: 4px;
}

.chat-input-bar {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-primary);
}

/* ============================================
   Grid Layout Utilities
   ============================================ */

.row {
  display: flex;
  flex-wrap: wrap;
  margin: -8px;
}

.col { padding: 8px; flex: 1; }
.col-3 { padding: 8px; width: 25%; }
.col-4 { padding: 8px; width: 33.333%; }
.col-6 { padding: 8px; width: 50%; }
.col-8 { padding: 8px; width: 66.666%; }
.col-9 { padding: 8px; width: 75%; }
.col-12 { padding: 8px; width: 100%; }

.gap-2 { gap: 8px; }
.gap-3 { gap: 16px; }
.gap-4 { gap: 24px; }

.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 16px; }
.mb-4 { margin-bottom: 24px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }

/* ============================================
   AG-Grid Customization
   ============================================ */

.ag-theme-alpine {
  --ag-font-family: 'Inter', system-ui, sans-serif;
  --ag-font-size: 13px;
  --ag-border-color: var(--border-subtle);
  --ag-header-background-color: var(--bg-secondary);
  --ag-odd-row-background-color: var(--bg-primary);
  --ag-row-hover-color: var(--bg-secondary);
  --ag-selected-row-background-color: var(--primary-50);
  --ag-range-selection-border-color: var(--primary-500);
  --ag-checkbox-checked-color: var(--primary-500);
  --ag-alpine-active-color: var(--primary-500);
}

/* ============================================
   Scrollbar
   ============================================ */

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-strong);
}

/* ============================================
   Animations
   ============================================ */

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.loading-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

/* ============================================
   Responsive
   ============================================ */

@media (max-width: 1024px) {
  .sidebar { width: 240px; }
  .metric-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .app-layout { flex-direction: column; }
  .sidebar { width: 100%; height: auto; max-height: 40vh; }
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .content { padding: 16px; }
  .tab-bar { padding: 0 16px; }
  .topbar { padding: 12px 16px; }
}
```

### 2.6 New: `static/js/main.js` — Enhanced Core JavaScript

```javascript
// ============================================
// FINESE 2 — Core JavaScript
// ============================================

// Toast notifications
function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const iconSvg = type === 'success' 
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>'
        : type === 'error'
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    
    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Dataset info loader
async function loadDatasetInfo() {
    try {
        const res = await fetch('/api/data/info');
        const data = await res.json();
        const card = document.getElementById('datasetCard');
        const badge = document.getElementById('datasetBadge');
        
        if (data.loaded) {
            card.innerHTML = `
                <div class="dataset-info">
                    <div class="dataset-name" title="${data.name}">${data.name}</div>
                    <div class="dataset-meta">${data.shape[0].toLocaleString()} rows · ${data.shape[1]} columns</div>
                    <div class="dataset-shape">
                        <span class="shape-badge">${data.shape[0]} R</span>
                        <span class="shape-badge">${data.shape[1]} C</span>
                    </div>
                </div>
            `;
            if (badge) {
                badge.style.display = 'inline-flex';
                badge.textContent = data.name;
            }
        } else {
            card.innerHTML = `
                <div class="dataset-empty">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                    <span>No dataset loaded</span>
                </div>
            `;
            if (badge) badge.style.display = 'none';
        }
    } catch (e) {
        console.error('Failed to load dataset info:', e);
    }
}

// File upload handling
function initUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    if (!zone || !input) return;
    
    zone.addEventListener('click', () => input.click());
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) handleFileUpload(files[0]);
    });
    
    input.addEventListener('change', (e) =>