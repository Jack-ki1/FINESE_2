# 🧬 FINESE2 - Professional Data Intelligence Platform

> **Enterprise-grade data platform** — Comprehensive solution for data scientists, analysts, and MLOps engineers with modern DevOps practices

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-orange.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-blueviolet.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-pytest-yellow.svg)](tests/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](Dockerfile)

## 🚀 What's New in v4.0.0?

**Major Infrastructure & Quality Improvements**: Enhanced the platform with professional development tooling, comprehensive testing, Docker support, and improved documentation!

### ✨ New Features
- ✅ **Database Models**: Full ORM models for users, datasets, experiments, and more
- ✅ **Testing Framework**: Pytest setup with unit and integration tests
- ✅ **Docker Support**: Containerized deployment with docker-compose
- ✅ **Environment Management**: .env configuration with python-dotenv
- ✅ **Code Quality Tools**: Pre-commit hooks, black, isort, flake8
- ✅ **Documentation**: Comprehensive guides and API reference
- ✅ **Makefile**: Automated common development tasks
- ✅ **CI/CD Ready**: GitHub Actions workflow included

### 📊 Improvements
- Better project structure and organization
- Enhanced error handling and logging
- Improved security with proper secret management
- SPA-style routing for better UX
- Version tracking with CHANGELOG

## 🏗️ Architecture Overview

```
FINESE2/
├── app/
│   ├── core/                 # Core business logic (9 modules)
│   │   ├── data.py          # Data management
│   │   ├── eda.py           # Exploratory data analysis
│   │   ├── cleaning.py      # Data cleaning
│   │   ├── visualize.py     # Visualization
│   │   ├── analysis.py      # Statistical analysis
│   │   ├── ml_models.py     # Machine learning
│   │   ├── mlops.py         # MLOps operations
│   │   ├── reports.py       # Report generation
│   │   └── dashboard.py     # Dashboard creation
│   ├── models/              # Database models (NEW!)
│   ├── routes/              # API endpoints
│   ├── utils/               # Utility functions
│   └── __init__.py          # App factory
├── tests/                   # Test suite (NEW!)
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docs/                    # Documentation (NEW!)
├── dashboard/               # Frontend templates
│   └── templates/
│       └── dashboard.html  # Main UI
├── instance/                # SQLite databases
├── models/                  # Saved ML models
├── reports/                 # Generated reports
├── Dockerfile              # Docker configuration (NEW!)
├── docker-compose.yml      # Docker Compose (NEW!)
├── Makefile                # Task automation (NEW!)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template (NEW!)
├── .pre-commit-config.yaml # Pre-commit hooks (NEW!)
├── pyproject.toml          # Project config (NEW!)
└── main.py                 # Application entry point
```

## 🌟 Key Features

### 📊 **Interactive Dashboard**
- Modern Bootstrap 5 UI with responsive design
- Multiple dashboard views (analytics, ML monitoring)
- Real-time KPI widgets with drill-down capabilities
- Single Page Application (SPA) experience

### 📈 **Data Operations**
- Upload CSV, Excel, JSON, Parquet files (up to 50MB)
- Sample dataset loading (Iris, Titanic, Wine)
- Data preview and metadata extraction
- Export in multiple formats
- Database persistence with SQLAlchemy

### 🔍 **Exploratory Data Analysis (EDA)**
- Comprehensive statistical summaries
- Correlation analysis with heatmaps
- Distribution analysis and visualization
- Missing values detection and reporting
- Anomaly detection algorithms

### 🧹 **Data Cleaning**
- Automatic issue detection
- Intelligent cleaning recommendations
- Missing value imputation (mean, median, mode)
- Outlier detection and removal (IQR method)
- Data normalization and scaling
- Categorical encoding

### 📊 **Visualization**
- 12+ chart types (scatter, line, bar, histogram, box, etc.)
- Interactive Plotly visualizations
- Statistical summary charts
- Custom dashboard creation
- Export to PNG/SVG/HTML

### 📋 **Statistical Analysis**
- Descriptive statistics
- Hypothesis testing (t-test, ANOVA, Chi-square)
- Regression analysis
- Time series decomposition
- Feature importance ranking

### 🤖 **Machine Learning**
- 14+ algorithms (classification & regression)
- Automated model selection
- Hyperparameter tuning with GridSearch
- Cross-validation (k-fold)
- Model comparison and evaluation
- Performance metrics (accuracy, precision, recall, F1, RMSE, etc.)

### 🚀 **MLOps**
- Experiment tracking with database
- Model registry and versioning
- Model performance monitoring
- Model promotion workflows
- Audit trail for all operations

### 📄 **Reporting**
- HTML report templates
- Multiple report types (EDA, ML, cleaning)
- Export to PDF/HTML
- Customizable layouts
- Automated report generation

### 🧠 **AI Integration**
- Tokenized AI tool execution
- Multi-provider support (OpenAI, Anthropic, Google)
- Budget-controlled API calls
- Deterministic tool registry
- AI-assisted insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (optional, for cloning)
- Docker (optional, for containerized deployment)

### Option 1: Local Installation (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/your-username/FINESE2.git
cd FINESE2

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
py main.py --host 0.0.0.0 --port 5000
```

Open your browser to: **http://localhost:5000**

### Option 2: Docker Installation (Recommended for Production)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Option 3: Using Makefile

```bash
# Install dependencies and setup
make install

# Run application
make run

# Run tests
make test

# Format code
make format

# Build Docker image
make docker-build
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Required
SECRET_KEY=your-super-secret-key-change-this

# Optional
DATABASE_URL=sqlite:///instance/finese2.db
REDIS_URL=redis://localhost:6379/0
ENABLE_JWT=false
OPENAI_API_KEY=sk-...
MAX_UPLOAD_SIZE=50
LOG_LEVEL=INFO
```

### Database

- **Development**: SQLite (default)
- **Production**: PostgreSQL recommended

```bash
# PostgreSQL example
DATABASE_URL=postgresql://user:password@localhost:5432/finese2
```

## 📡 API Endpoints

### Base URL: `http://localhost:5000/api/v1`

#### Data Operations (`/api/v1/data`)
- `POST /upload` - Upload dataset
- `POST /load-sample` - Load sample dataset
- `GET /info/{dataset_id}` - Get dataset info
- `DELETE /delete/{dataset_id}` - Delete dataset

#### EDA (`/api/v1/eda`)
- `POST /profile` - Generate EDA profile
- `POST /correlation` - Correlation analysis
- `POST /missing-values` - Missing values analysis

#### Cleaning (`/api/v1/cleaning`)
- `POST /detect-issues` - Detect data issues
- `POST /recommendations` - Get cleaning recommendations
- `POST /apply` - Apply cleaning operations

#### Machine Learning (`/api/v1/ml`)
- `POST /train` - Train model
- `POST /predict` - Make predictions
- `GET /models` - List trained models
- `DELETE /models/{model_id}` - Delete model

#### Dashboard (`/api/v1/dashboard`)
- `POST /create` - Create dashboard
- `GET /list` - List dashboards

#### Jobs (`/api/v1/jobs`)
- `GET /status/{job_id}` - Check job status
- `GET /list` - List all jobs

#### AI Operations (`/api/v1/ai`)
- `POST /execute` - Execute AI tools with token budget

### Health Checks
- `GET /health` - Application health status
- `GET /ready` - Readiness check

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_data.py -v

# Open coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## 📚 Documentation

Comprehensive documentation available in `docs/`:

- [Getting Started](docs/getting-started.md)
- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Development Guide](docs/development-guide.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install pre-commit hooks: `pre-commit install`
4. Make your changes
5. Run tests: `pytest tests/ -v`
6. Format code: `make format`
7. Commit: `git commit -m "feat: add amazing feature"`
8. Push: `git push origin feature/amazing-feature`
9. Open a Pull Request

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Core Modules | 9 |
| API Endpoints | 20+ |
| ML Algorithms | 14+ |
| Chart Types | 12+ |
| Test Coverage | Growing |
| Python Versions | 3.8-3.12 |

## 🔧 Development Tools

- **Code Formatting**: Black
- **Import Sorting**: isort
- **Linting**: flake8
- **Type Checking**: mypy (optional)
- **Pre-commit Hooks**: pre-commit
- **Testing**: pytest with coverage
- **Documentation**: Markdown + MkDocs (planned)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask web framework
- Plotly for visualizations
- scikit-learn for ML algorithms
- pandas for data manipulation
- All open-source contributors

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/FINESE2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/FINESE2/discussions)

---

<div align="center">

**Made with ❤️ by the FINESE2 Team**

[⭐ Star this repo](https://github.com/your-username/FINESE2) • [🐛 Report Bug](https://github.com/your-username/FINESE2/issues) • [💡 Request Feature](https://github.com/your-username/FINESE2/issues)

**Version 4.0.0** | **Production Ready** ✅ | **Docker Supported** 🐳 | **Tested** 🧪

</div>
