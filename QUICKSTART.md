# FINESE2 Quick Start Guide

Get up and running with FINESE2 in under 5 minutes!

## 🚀 Super Quick Start (3 Commands)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment file
cp .env.example .env

# 3. Run the application
py main.py --host 0.0.0.0 --port 5000
```

Open http://localhost:5000 in your browser! 🎉

---

## 📋 Detailed Setup

### Step 1: Prerequisites Check

Ensure you have:
- ✅ Python 3.8 or higher (`python --version`)
- ✅ pip installed (`pip --version`)
- ✅ Git (optional, for cloning)

### Step 2: Get the Code

**If you haven't cloned yet:**
```bash
git clone https://github.com/your-username/FINESE2.git
cd FINESE2
```

**If you already have the code:**
```bash
cd FINESE2
```

### Step 3: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, pandas, scikit-learn, plotly, and all other required packages.

### Step 5: Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env file (optional but recommended)
# At minimum, change SECRET_KEY to a random string
```

**Quick .env setup:**
```bash
SECRET_KEY=change-this-to-random-string-12345
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/finese2.db
```

### Step 6: Run the Application

```bash
py main.py --host 0.0.0.0 --port 5000
```

You should see:
```
============================================================
FINESE2 - Professional Data Intelligence Platform
Version: 4.0.0
Environment: development
Host: 0.0.0.0
Port: 5000
Debug: False
============================================================
```

### Step 7: Open Your Browser

Navigate to: **http://localhost:5000**

You should see the FINESE2 dashboard! 🎊

---

## 🎯 First Tasks

### 1. Upload a Dataset
1. Click "Upload Data" button
2. Select a CSV file (or use sample data)
3. Wait for processing

### 2. Explore Data
- View statistics in the overview panel
- Check data quality metrics
- Examine column distributions

### 3. Run EDA
- Click "Generate EDA Report"
- Review correlations and missing values
- Download the report

### 4. Train a Model
- Select target variable
- Choose algorithm (or use auto-select)
- Click "Train Model"
- View results and metrics

---

## 🐳 Docker Quick Start (Alternative)

If you prefer Docker:

```bash
# One command to rule them all
docker-compose up -d

# Access at http://localhost:5000
```

To stop:
```bash
docker-compose down
```

---

## 🧪 Testing

Verify everything works:

```bash
# Run tests
pytest tests/ -v

# Should see all tests passing ✅
```

---

## 🔧 Common Issues & Solutions

### Issue: "Module not found"
**Solution:** Make sure virtual environment is activated
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Issue: "Port 5000 already in use"
**Solution:** Use a different port
```bash
py main.py --host 0.0.0.0 --port 5001
```

### Issue: "Database initialization failed"
**Solution:** Delete old database and restart
```bash
# Windows
del instance\finese2.db

# macOS/Linux
rm instance/finese2.db

# Then restart the app
py main.py --host 0.0.0.0 --port 5000
```

### Issue: "ImportError: No module named 'dotenv'"
**Solution:** Install python-dotenv
```bash
pip install python-dotenv
```

---

## 📚 Next Steps

Now that you're running FINESE2:

1. **Read the full documentation**: [docs/getting-started.md](docs/getting-started.md)
2. **Explore API endpoints**: [README.md#api-endpoints](README.md#-api-endpoints)
3. **Learn about features**: [README.md#key-features](README.md#-key-features)
4. **Contribute to the project**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💡 Pro Tips

### Enable Debug Mode
```bash
py main.py --host 0.0.0.0 --port 5000 --debug
```

### Use Sample Data
No dataset? Load built-in samples:
- Iris dataset
- Titanic dataset
- Wine quality dataset

### Keyboard Shortcuts
- `Ctrl+C` - Stop the server
- `F5` - Refresh dashboard
- `Ctrl+R` - Reload page

### Performance Tips
- Keep datasets under 100MB for best performance
- Use Parquet format for faster loading
- Enable Redis caching for production

---

## 🆘 Need Help?

- **Documentation**: Check [docs/](docs/) folder
- **Issues**: [GitHub Issues](https://github.com/your-username/FINESE2/issues)
- **Questions**: [GitHub Discussions](https://github.com/your-username/FINESE2/discussions)

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Application starts without errors
- [ ] http://localhost:5000 loads the dashboard
- [ ] Health check works: http://localhost:5000/health
- [ ] Can upload a sample dataset
- [ ] Tests pass: `pytest tests/ -v`

All checked? You're ready to go! 🚀

---

**Happy Data Science!** 📊🤖
