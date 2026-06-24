# Getting Started with FINESE2

This guide will help you get FINESE2 up and running on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (Python package manager)
- **Git** ([Download](https://git-scm.com/))
- **Docker** (optional, for containerized deployment)

## Installation

### Option 1: Local Installation (Recommended for Development)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/FINESE2.git
   cd FINESE2
   ```

2. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Copy the example env file
   cp .env.example .env
   
   # Edit .env with your configuration
   # At minimum, set SECRET_KEY
   ```

5. **Run the application**:
   ```bash
   py main.py --host 0.0.0.0 --port 5000
   ```

6. **Open your browser**:
   Navigate to `http://localhost:5000`

### Option 2: Docker Installation (Recommended for Production)

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Access the application**:
   Navigate to `http://localhost:5000`

## First Steps

### 1. Upload a Dataset

- Click "Upload Data" in the dashboard
- Select a CSV, Excel, JSON, or Parquet file
- Wait for processing to complete

### 2. Explore Your Data

- View automatic statistics
- Check data quality metrics
- Examine distributions

### 3. Run EDA

- Generate comprehensive EDA reports
- View correlation matrices
- Identify missing values

### 4. Train a Model

- Select target variable
- Choose algorithm (or use auto-select)
- Train and evaluate

## Configuration

### Environment Variables

Key environment variables you can configure in `.env`:

```bash
# Application
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///instance/finese2.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# AI Providers (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Database

By default, FINESE2 uses SQLite for simplicity. For production, consider PostgreSQL:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/finese2
```

## Common Commands

```bash
# Run tests
pytest tests/ -v

# Format code
black app/ tests/
isort app/ tests/

# Run linters
flake8 app/ tests/

# Build Docker image
docker build -t finese2:latest .

# Clean up temporary files
make clean
```

## Next Steps

- Read the [Architecture Overview](architecture.md) to understand the system design
- Explore the [API Reference](api-reference.md) for programmatic access
- Check the [Development Guide](development-guide.md) to contribute

## Troubleshooting

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review console logs for error messages
3. Search existing [GitHub Issues](https://github.com/your-username/FINESE2/issues)
4. Create a new issue if needed

## Support

- **Documentation**: You're reading it!
- **Community**: GitHub Discussions
- **Issues**: GitHub Issues
- **Email**: support@finese2.com (if applicable)

---

Happy analyzing! 🚀
