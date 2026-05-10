# FINESE - Smart Data Explorer Pro

A comprehensive, modular data analysis platform with AI-powered insights, automated cleaning, modeling, and export capabilities.

---

## 📊 Overview

FINESE is a powerful data intelligence platform that transforms raw datasets into actionable insights without writing code. The architecture features a FastAPI backend with a React frontend, providing better performance, scalability, and maintainability compared to traditional solutions.

---

## ✨ Key Features

### 🔍 **Intelligent Data Review**
- Automatic data profiling and quality assessment
- Visual data summaries with key metrics
- Missing value and duplicate detection
- Interactive data exploration

### 🧹 **Smart Data Cleaning**
- Automated type detection and conversion suggestions
- Bulk apply cleaning transformations
- Side-by-side preview of changes
- Reversible cleaning operations

### 📊 **Interactive Charts & Visualizations**
- Drag-and-drop chart builder
- Multiple visualization types (bar, line, scatter, histograms, heatmaps)
- Dynamic filtering and drill-down capabilities
- Export charts in multiple formats

### 💬 **AI-Powered Chatbot**
- Natural language queries about your data
- Supports OpenAI, Anthropic, and Google Gemini APIs
- Rule-based engine for offline use
- Automated insight generation

### 🧠 **Machine Learning Studio**
- Automated feature engineering
- Model selection and comparison
- Hyperparameter optimization
- Model interpretability and SHAP explanations
- Export models and code

### 📤 **Comprehensive Export Options**
- Export cleaned data in multiple formats (CSV, Excel, JSON)
- Professional PDF and PowerPoint reports
- Model export (joblib, pickle)
- Production-ready Python code generation

### 🗣️ **SQL Query Interface**
- Query your data using standard SQL syntax
- Schema explorer for easy column discovery
- Download query results as CSV
- Powered by DuckDB for fast analytics

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Frontend** | React, TailwindCSS, Framer Motion, Recharts, Plotly | Modern, responsive UI with animations and visualizations |
| **Backend** | FastAPI, Uvicorn, Pydantic | High-performance API with data validation |
| **Data Processing** | Pandas, NumPy, DuckDB, ydata-profiling | Efficient data manipulation and analysis |
| **Visualization** | Plotly, Recharts | Interactive data visualization |
| **ML** | Scikit-learn, XGBoost, LightGBM, CatBoost | Machine learning algorithms |
| **Reports** | ReportLab, Python-PPTX | PDF and PowerPoint report generation |
| **AI** | OpenAI, Anthropic, Google Gemini APIs | AI-powered insights and natural language processing |
| **Caching** | Redis (optional) | In-memory data caching |
| **Job Queue** | Celery (optional) | Task queue for background jobs |
| **Database** | SQLite (with option to upgrade to PostgreSQL) | Data storage and persistence |

---

## 📁 Folder Structure

```
FINESE_2/
├── backend/
│   ├── main.py                   # FastAPI application entrypoint
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend Docker configuration
│   └── api/
│       ├── __init__.py
│       ├── routers/              # API route handlers
│       │   ├── auth.py
│       │   ├── charts.py
│       │   ├── datasets.py
│       │   ├── export.py
│       │   ├── health.py
│       │   ├── jobs.py
│       │   ├── ml_models.py
│       │   ├── sql_query.py
│       │   └── ...
│       ├── schemas/              # Pydantic models
│       │   ├── auth.py
│       │   ├── charts.py
│       │   ├── datasets.py
│       │   ├── health.py
│       │   ├── jobs.py
│       │   ├── ml_models.py
│       │   ├── sql.py
│       │   └── ...
│       ├── services/             # Business logic
│       │   ├── cache_service.py
│       │   ├── chart_service.py
│       │   ├── dataset_service.py
│       │   ├── export_service.py
│       │   ├── health_service.py
│       │   ├── job_service.py
│       │   ├── ml_service.py
│       │   └── sql_service.py
│       └── core/                 # Configuration and utilities
│           ├── __init__.py
│           ├── config.py
│           └── dependencies.py
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.js
│   │   │   └── Sidebar.js
│   │   ├── tabs/
│   │   │   ├── ChartsTab.js
│   │   │   ├── ChatbotTab.js
│   │   │   ├── CleaningTab.js
│   │   │   ├── ExportTab.js
│   │   │   ├── ModelTab.js
│   │   │   ├── ReviewTab.js
│   │   │   └── SqlTab.js
│   │   ├── App.js
│   │   ├── index.css
│   │   └── index.js
│   ├── package.json
│   ├── Dockerfile                # Frontend Docker configuration
│   ├── nginx.conf
│   └── tailwind.config.js
├── docker-compose.yml            # Docker Compose configuration
├── README.md                     # This file
└── README_FASTAPI.md             # FastAPI specific documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose (for containerized deployment)
- pip and npm package managers

---

### Quick Start with Docker Compose (Recommended)

The easiest way to run the full application stack is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-repo/FINESE_2.git
cd FINESE_2

# Build and start all services
docker-compose up --build

# The application will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Backend API Documentation: http://localhost:8000/docs
```

---

### Manual Installation

#### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (optional but recommended for AI features):
   Create a `.env` file in the backend directory with your API keys:
   ```bash
   OPENAI_API_KEY="your-openai-key"
   ANTHROPIC_API_KEY="your-anthropic-key"
   GOOGLE_GEMINI_API_KEY="your-google-key"
   REDIS_URL="redis://localhost:6379/0"
   DATABASE_URL="sqlite:///./finese.db"
   SECRET_KEY="your-secret-key-here"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will be available at http://localhost:8000

---

#### Frontend (React)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. The frontend will be available at http://localhost:3000

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# API Keys for AI Services
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
GOOGLE_GEMINI_API_KEY="your-google-key"

# Database Configuration
DATABASE_URL="sqlite:///./finese.db"

# Security Settings
SECRET_KEY="a-very-secret-key-here-make-it-long-and-random"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Configuration (for caching and job queues)
REDIS_URL="redis://localhost:6379/0"

# Optional: External Service URLs
EXTERNAL_SERVICE_BASE_URL="http://localhost:8000"
```

---

### Available Scripts

#### Backend Scripts

- `uvicorn main:app --reload`: Run the development server
- `python -m pytest`: Run backend tests (if available)
- `python -m black .`: Format code with Black (if installed)

#### Frontend Scripts

- `npm start`: Runs the app in development mode
- `npm run build`: Builds the app for production
- `npm test`: Launches the test runner
- `npm run eject`: Ejects from Create React App (irreversible)

---

## 🚀 API Endpoints

The backend exposes the following API endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/datasets/` - Upload dataset
- `GET /api/v1/datasets/{dataset_id}` - Get dataset summary
- `POST /api/v1/datasets/{dataset_id}/filters` - Apply filters to dataset
- `GET /api/v1/datasets/{dataset_id}/preview` - Preview dataset
- `GET /api/v1/health/{dataset_id}` - Get data health score
- `POST /api/v1/health/{dataset_id}/auto-insights` - Generate auto insights
- `GET /api/v1/charts/{dataset_id}` - Generate charts
- `GET /api/v1/ml_models/{dataset_id}` - Train ML models
- `POST /api/v1/export/{dataset_id}` - Export data/models/reports
- `POST /api/v1/sql_query/{dataset_id}` - Execute SQL queries on dataset

API documentation is available at http://localhost:8000/docs when the backend is running.

---

## 🐳 Docker Configuration

The project includes Dockerfiles for both backend and frontend, as well as a docker-compose.yml file for easy orchestration:

### Services in docker-compose.yml

- **backend**: FastAPI application running on port 8000
- **frontend**: Nginx serving React application on port 3000
- **redis**: Redis server for caching and job queues on port 6379

---

### Building Custom Images

To build the images individually:

**Backend:**
```bash
cd backend
docker build -t finese-backend .
```

**Frontend:**
```bash
cd frontend
docker build -t finese-frontend .
```

---

## 🤝 Contributing

We welcome contributions to the FINESE project! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure your code follows the project's style guidelines
5. Add documentation for new features
6. Include tests for new functionality
7. Update README if necessary

---

## 🧪 Testing

### Backend Tests

Run backend tests with pytest (if tests exist):

```bash
cd backend
python -m pytest
```

### Frontend Tests

Run frontend tests:

```bash
cd frontend
npm test
```

---

## 🌐 GitHub Pages Deployment

This project can be deployed to GitHub Pages. However, note that GitHub Pages only hosts static files, so the backend API must be hosted separately.

### Steps for GitHub Pages Deployment:

1. Set up the backend API on a separate hosting provider (Heroku, AWS, Azure, etc.)

2. Update the frontend's `.env.production` file with the correct API endpoint:
   ```
   REACT_APP_API_BASE_URL=https://your-backend-api-domain.com
   ```

3. The GitHub Actions workflow (located at `.github/workflows/deploy.yml`) will automatically deploy the frontend to GitHub Pages when you push to the main branch.

4. To customize the workflow for your repository:
   - Update the `PUBLIC_URL` in the workflow file if needed
   - The site will be deployed to `https://your-username.github.io/repository-name`

### Important Notes for GitHub Pages:

- The backend API must be hosted separately and accessible via HTTPS
- Enable CORS on your backend to allow requests from your GitHub Pages domain
- Consider implementing authentication if sensitive data is involved
- Update API endpoints in the frontend to point to your hosted backend

## 🚢 Deployment

### Production Deployment with Docker

For production deployments, consider the following:

1. Use environment variables for secrets instead of hardcoding them
2. Configure a reverse proxy (like Nginx) in front of the services
3. Set up SSL certificates for HTTPS
4. Configure persistent storage for databases and uploaded files
5. Monitor logs and performance metrics

---

### Manual Deployment

1. Build the frontend: `cd frontend && npm run build`
2. Copy the build directory to the backend static directory
3. Deploy the backend with all dependencies
4. Configure a WSGI server like Gunicorn for production

### GitHub Pages Deployment

For GitHub Pages deployment:
1. Set up your backend API on a separate host
2. Configure frontend environment variables with your API endpoint
3. Push to main branch to trigger GitHub Actions deployment workflow

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

If you encounter issues or have questions:

1. Check the API documentation at `/docs` endpoint
2. Review the project issues on GitHub
3. Submit a new issue if you can't find a solution
4. Consult the README files for specific components

---

Made with ❤️ by the FINESE Team

Transform your data into insights with FINESE!