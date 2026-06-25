# FINESE 2 - Smart Data Explorer Pro (Flask Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-310/)
[![Flask](https://img.shields.io/badge/flask-3.0+-black.svg)](https://flask.palletsprojects.com/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)

**FINESE 2** (Fast Intelligent NEural Statistical Engine) is a comprehensive, Flask-based data analysis platform with AI-powered insights, automated cleaning, modeling, and export capabilities. Transform raw datasets into actionable insights through a modern web dashboard without writing code.

## 🎯 Overview

FINESE 2 is a powerful data intelligence platform that transforms raw datasets into actionable insights without writing code. Built on Flask with a Bootstrap frontend, it provides a seamless workflow for exploring, cleaning, analyzing, and presenting data through an intuitive web interface.

The application features seven integrated modules for different data analysis tasks:

| Feature Module | Description |
|----------------|-------------|
| **Review** | Automatic data profiling, quality assessment, and visual summaries |
| **Cleaning** | Smart type detection, issue identification, and bulk transformations |
| **Charts & Pivot** | Interactive Plotly visualizations with drag-and-drop builder |
| **Chatbot** | Natural language queries powered by OpenAI, Anthropic, or Gemini |
| **ML Studio** | Automated machine learning with model training and evaluation |
| **SQL** | DuckDB-powered SQL query interface with schema explorer |
| **Export** | Download cleaned data in CSV, Excel, or JSON formats |

## ✨ Key Features

### 🔍 **Intelligent Data Review**
- Automatic data profiling with key metrics (rows, columns, nulls, duplicates, memory)
- Top/bottom row previews using AG-Grid interactive tables
- Data type detection and summary statistics
- Real-time dataset information in sidebar

### 🧹 **Smart Data Cleaning**
- Automated issue detection (numeric-as-text, date-as-text patterns)
- Severity-based recommendations with one-click fixes
- Bulk apply transformations (to_numeric, to_datetime, drop_na)
- Preview changes before applying
- Persistent cleaning log across sessions

### 📊 **Interactive Charts & Visualizations**
- Five chart types: Bar, Line, Scatter, Histogram, Box plots
- Dynamic column selection for X, Y, and Color axes
- Plotly-powered interactive charts with zoom, pan, and hover
- Clean white template styling for professional presentations

### 💬 **AI-Powered Chatbot**
- Natural language queries about your dataset
- Multi-model support: OpenAI GPT, Anthropic Claude, Google Gemini
- Context-aware responses with dataset metadata
- Persistent chat history within session
- Extensible architecture for custom LLM integration

### 🧠 **Machine Learning Studio**
- Model training interface with target column selection
- Support for classification and regression tasks
- Real-time progress tracking with visual progress bar
- Job-based asynchronous training with status polling
- Results display with accuracy metrics and model details

### 🗣️ **SQL Query Interface**
- Standard SQL syntax support via DuckDB engine
- Schema explorer showing all columns with data types
- Instant query execution with AG-Grid result display
- Sortable, filterable, resizable result columns
- Error handling with descriptive messages

### 📤 **Comprehensive Export Options**
- One-click downloads in three formats: CSV, Excel, JSON
- Automatic filename generation from original dataset
- In-memory streaming for efficient large file handling
- Proper MIME types for browser compatibility

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask 3.0+ with Blueprint architecture
- **Session Management**: Flask-Session (filesystem backend)
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **Database Engine**: DuckDB 0.9+ for SQL queries
- **Serialization**: Pickle for server-side DataFrame persistence

### Frontend
- **UI Framework**: Bootstrap 5.3.2
- **Data Grids**: AG-Grid Community 31.0.0
- **Visualizations**: Plotly.js 2.27.0
- **JavaScript**: Vanilla ES6+ with async/await

### Machine Learning & AI
- **ML Libraries**: Scikit-learn 1.3+, XGBoost 2.0+, LightGBM 4.0+, CatBoost 1.2+
- **LLM Providers**: OpenAI 1.0+, Anthropic 0.8+, Google Generative AI 0.3+
- **Report Generation**: ReportLab 4.0+, Python-PPTX 0.6+

### Architecture
- **Pattern**: Service-oriented with modular blueprints
- **State Management**: Server-side sessions with filesystem storage
- **Data Persistence**: Pickle-based DatasetStore for DataFrame caching
- **File Uploads**: 50MB limit with temporary storage

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **pip**: Latest version
- **Memory**: 4GB RAM minimum (8GB+ recommended for ML features)
- **Browser**: Modern browser with JavaScript enabled (Chrome, Firefox, Edge, Safari)

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/finese2.git
   cd finese2
   ```

2. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create required directories** (auto-created on first run, but can be manual):
   ```bash
   mkdir flask_session
   mkdir static/uploads
   ```

5. **Run the Flask application**:
   ```bash
   python app.py
   ```

6. **Open your browser**:
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Production Deployment (Gunicorn)

For production environments, use Gunicorn as the WSGI server:

1. **Install Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Run with multiple workers**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Environment variables** (create `.env` file):
   ```env
   SECRET_KEY=your-production-secret-key-here
   OPENAI_API_KEY=sk-your-openai-key
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
   GOOGLE_API_KEY=your-google-api-key
   ```

### Docker Deployment

Build and run using the included Dockerfile:

```bash
docker build -t finese2 .
docker run -p 5000:5000 -v $(pwd)/flask_session:/app/flask_session finese2
```

## 📁 Project Structure

```
FINESE2/
├── app.py                      # Flask entry point with blueprint registration
├── config.py                   # Global configuration constants
├── state.py                    # Flask session default values
├── requirements.txt            # Python dependencies
├── core/                       # Core data management (unchanged from v1)
│   ├── __init__.py
│   ├── dataset_context.py      # Original dataset context manager
│   └── dataset_store.py        # NEW: Server-side DataFrame persistence
├── services/                   # Business logic (unchanged from v1)
│   ├── __init__.py
│   ├── chart_service.py        # Chart generation logic
│   ├── cleaning_service.py     # Data cleaning algorithms
│   ├── health_service.py       # Data health scoring
│   ├── llm_service.py          # LLM integration
│   ├── ml_service.py           # Machine learning pipelines
│   ├── profiling_service.py    # Data profiling utilities
│   └── sql_service.py          # SQL query processing
├── routes/                     # NEW: Flask route blueprints
│   ├── __init__.py             # Blueprint exports
│   ├── data.py                 # File upload & dataset info
│   ├── review.py               # Data profiling endpoints
│   ├── cleaning.py             # Smart cleanup endpoints
│   ├── charts.py               # Visualization builder
│   ├── chatbot.py              # AI chat endpoints
│   ├── ml.py                   # ML training endpoints
│   ├── sql.py                  # SQL query endpoints
│   └── export.py               # File download endpoints
├── templates/                  # NEW: Jinja2 HTML templates
│   ├── base.html               # Master layout with sidebar
│   ├── review.html             # Data review dashboard
│   ├── cleaning.html           # Cleaning interface
│   ├── charts.html             # Chart builder
│   ├── chatbot.html            # Chat interface
│   ├── ml.html                 # ML studio
│   ├── sql.html                # SQL query editor
│   └── export.html             # Export options
├── static/                     # NEW: Static assets
│   ├── css/
│   │   └── style.css           # Custom styles
│   ├── js/
│   │   └── main.js             # Shared JavaScript
│   └── uploads/                # Temporary dataset storage
├── utils/                      # Utility functions (unchanged from v1)
│   ├── __init__.py
│   ├── data_utils.py           # Data manipulation helpers
│   ├── health_utils.py         # Health check utilities
│   ├── ml_utils.py             # ML helper functions
│   └── ui_utils.py             # UI rendering utilities
└── flask_session/              # Server-side session files (gitignored)
```

## 🔄 Migration from FINESE 1 (Streamlit)

FINESE 2 represents a complete migration from Streamlit to Flask while preserving 100% of backend logic:

### What Changed
- ✅ **Presentation Layer**: Streamlit → Flask + Bootstrap + Jinja2
- ✅ **Session Management**: `st.session_state` → Flask-Session (filesystem)
- ✅ **Data Persistence**: In-memory → Pickle-based DatasetStore
- ✅ **Routing**: Streamlit pages → Flask Blueprints
- ✅ **Frontend**: Streamlit widgets → Bootstrap components + AG-Grid + Plotly.js

### What Stayed the Same
- ✅ All [`services/`](c:\Users\PC\Desktop\PROJECTS\FINESE2\services) modules (zero changes)
- ✅ [`core/dataset_context.py`](c:\Users\PC\Desktop\PROJECTS\FINESE2\core\dataset_context.py) (unchanged)
- ✅ [`utils/`](c:\Users\PC\Desktop\PROJECTS\FINESE2\utils) utility functions (unchanged)
- ✅ All business logic and algorithms
- ✅ Feature parity across all 7 modules

### Benefits of Migration
- 🚀 Better performance with server-side rendering
- 🔒 Enhanced security with server-side sessions
- 📱 Responsive design works on mobile devices
- 🎨 Full control over HTML/CSS/JavaScript
- 🌐 Standard web architecture (easier deployment)
- 💾 Persistent sessions across page refreshes

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root for API keys and secrets:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=development  # Set to 'production' in production

# AI Provider Keys (optional, for chatbot features)
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-generative-ai-key

# Optional: Custom Session Lifetime (in hours)
SESSION_LIFETIME=2
```

### App Configuration

Key settings in [`app.py`](c:\Users\PC\Desktop\PROJECTS\FINESE2\app.py):

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB uploads
```

## 🧪 Testing

Run the test suite to verify installation:

```bash
# Test imports
python test_imports.py

# Test architecture
python test_architecture.py
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` |
| `KeyError: 'dataset_id'` | Clear browser cookies and refresh |
| Upload fails with 413 error | Increase `MAX_CONTENT_LENGTH` in [`app.py`](c:\Users\PC\Desktop\PROJECTS\FINESE2\app.py) |
| Charts don't render | Check internet connection for Plotly CDN |
| AG-Grid shows blank | Ensure div has explicit height in CSS |
| Session lost on refresh | Verify `flask_session/` directory exists and is writable |
| Import errors on startup | Delete `__pycache__/` folders and restart |

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code style
- Add docstrings to all new functions
- Update documentation for new features
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section above
2. Search existing [Issues](https://github.com/your-username/finese2/issues)
3. Create a new issue with:
   - Python version (`python --version`)
   - Operating system
   - Flask version (`pip show flask`)
   - Steps to reproduce
   - Error message and stack trace

## 🙏 Acknowledgments

- **Flask** team for the excellent web framework
- **Bootstrap** for the responsive UI components
- **Plotly** for interactive visualizations
- **AG-Grid** for powerful data grids
- **DuckDB** for fast analytical SQL
- **Hugging Face** for hosting the original Streamlit version
- The open-source community for invaluable packages

## 📈 Roadmap

Future enhancements planned:
- [ ] User authentication and multi-user support
- [ ] Database backend (PostgreSQL/MySQL) instead of pickle files
- [ ] Real-time collaboration features
- [ ] Advanced ML pipeline customization
- [ ] Custom report templates
- [ ] API endpoint exposure for programmatic access
- [ ] Plugin system for custom visualizations
- [ ] Dark mode theme

---

<div align="center">

**Built with ❤️ using Flask, Bootstrap, and Python**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/your-username/finese2/issues) · [Request Feature](https://github.com/your-username/finese2/issues)

</div>
