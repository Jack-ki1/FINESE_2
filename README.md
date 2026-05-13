# FINESE2 - Data Intelligence Platform

> Transform raw datasets into actionable insights without writing code.

A powerful, modern Streamlit-based data intelligence platform for data analysis, science, ML engineering, and data engineering workflows. FINESE2 provides an intuitive interface for data exploration, cleaning, visualization, modeling, and reporting.



###link to access the platform: https://huggingface.co/spaces/Jack-ki1/finese_data_2
## 🌟 Features

- **Data Ingestion**: Support for CSV, Excel, JSON, Parquet, SQL databases, and more
- **Auto EDA**: Automated exploratory data analysis with [ydata-profiling](https://github.com/ydataai/ydata-profiling), [Sweetviz](https://github.com/fbdesignpro/sweetviz), and custom analysis
- **Smart Cleaning**: Advanced data cleaning with recommendations for missing values, outliers, duplicates, scaling, and encoding
- **Visualization**: 15+ interactive Plotly charts with export capabilities
- **Statistical Analysis**: Hypothesis testing, regression, ANOVA, chi-square, and normality tests
- **Auto ML**: Classification, regression, clustering with model comparison and feature importance
- **MLOps**: Experiment tracking, model registry, leaderboards, and run comparison
- **Reports**: HTML, Excel, Word, and Markdown exports with professional templates
- **AI Assistant**: Multi-provider LLM support (OpenAI, Claude, Gemini, Ollama, Groq, Mistral, Azure, Custom)

## 📋 Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Features in Detail](#features-in-detail)
- [AI Assistant Providers](#ai-assistant-providers)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/FINESE2.git
   cd FINESE2
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

4. Run the application:
   ```bash
   streamlit run FINESE2.py
   ```

## Usage

The application is organized into several Streamlit pages accessible from the sidebar:

1. **Data**: Upload and manage datasets (CSV, Excel, JSON, etc.)
2. **EDA**: Perform automated exploratory data analysis
3. **Cleaning**: Apply smart cleaning techniques to your data
4. **Visualization**: Create interactive visualizations
5. **Analysis**: Conduct statistical analysis
6. **Modeling**: Build and compare machine learning models
7. **MLOps**: Track experiments and manage models
8. **Reports**: Generate professional reports
9. **AI Assistant**: Consult the AI for data insights

### Quick Start

1. Upload your dataset in the **Data** section
2. Run EDA to understand your data
3. Clean your data using the **Cleaning** tools
4. Visualize patterns in your data
5. Build ML models in the **Modeling** section
6. Generate reports and track experiments

## Architecture

```
FINESE2/
├── FINESE2.py              # Main entry point and home dashboard
├── modules/                # Core engines
│   ├── ai_assistant.py     # Multi-provider LLM interface
│   ├── data_manager.py     # Data ingestion and management
│   ├── eda_engine.py       # Automated EDA engine
│   ├── cleaner.py          # Data cleaning utilities
│   ├── visualizer.py       # Interactive visualizations
│   ├── analyzer.py         # Statistical analysis tools
│   ├── ml_modeler.py       # Machine learning modeling
│   ├── mlops_tracker.py    # Experiment tracking and model registry
│   └── report_generator.py # Report generation utilities
├── pages/                  # Streamlit pages (sidebar sections)
│   ├── 01_Data.py
│   ├── 02_EDA.py
│   ├── 03_Cleaning.py
│   ├── 04_Visualization.py
│   ├── 05_Analysis.py
│   ├── 06_Modeling.py
│   ├── 07_MLOps.py
│   ├── 08_Reports.py
│   └── 09_AI_Assistant.py
├── utils/                  # Utility functions
│   ├── session_state.py    # Session state management
│   ├── styling.py          # UI styling and components
│   ├── helpers.py          # Helper functions
│   ├── notifications.py    # Notification system
│   ├── search.py           # Search functionality
│   └── data_dictionary.py  # Data dictionary utilities
└── .streamlit/             # Streamlit configuration
    └── config.toml
```

## Features in Detail

### Data Ingestion
- Import from various formats: CSV, Excel, JSON, Parquet, SQL databases
- Connect to cloud storage services
- Sample datasets for experimentation
- Automatic data type detection

### Automated EDA
- Comprehensive statistical profiling
- Distribution analysis for numerical and categorical variables
- Correlation matrices and heatmaps
- Missing value analysis
- Outlier detection
- Data quality assessment

### Smart Data Cleaning
- Automated identification of data quality issues
- Missing value imputation strategies
- Outlier detection and treatment
- Duplicate removal
- Data type corrections
- Scaling and normalization options
- Categorical encoding (one-hot, label, ordinal)

### Visualization
- 15+ interactive chart types powered by Plotly
- Scatter plots, histograms, box plots, bar charts, heatmaps
- Time series visualization
- Distribution plots
- Correlation visualizations
- Customizable aesthetics and layouts
- Export to various formats

### Statistical Analysis
- Hypothesis testing (t-test, chi-square, ANOVA)
- Regression analysis
- Normality tests
- Correlation analysis
- Confidence intervals
- Effect size calculations

### Auto ML
- Automated model selection and hyperparameter tuning
- Classification algorithms (Random Forest, XGBoost, Logistic Regression, etc.)
- Regression algorithms (Linear Regression, SVR, Neural Networks, etc.)
- Clustering algorithms (K-Means, DBSCAN, Hierarchical)
- Cross-validation and model evaluation
- Feature importance analysis
- Model comparison leaderboards

### MLOps
- Experiment tracking with metadata logging
- Model versioning and registry
- Performance metric comparison
- Model deployment preparation
- Reproducibility features

### Reports
- HTML reports with interactive elements
- Excel spreadsheets with formatted tables
- Word documents with analysis summaries
- Markdown reports for documentation
- Professional templates

### AI Assistant
- Multi-provider LLM support
- Natural language queries about your data
- Automated insights and recommendations
- Code generation assistance
- Explanation of statistical results

## AI Assistant Providers

| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, o1, o3 |
| Anthropic | Claude 3.5 Sonnet, Opus, Haiku |
| Google | Gemini 1.5 Pro, Flash |
| Azure | GPT-4o, GPT-4 |
| Ollama | Llama, Mistral, Phi (local) |
| Groq | Llama 3.1, Mixtral |
| Mistral | Mistral Large, Medium |
| Custom | Any OpenAI-compatible API |

## Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Machine Learning**: Scikit-learn, XGBoost, LightGBM
- **Deep Learning**: TensorFlow/Keras, PyTorch (optional)
- **EDA**: ydata-profiling, Sweetviz
- **LLM Integration**: OpenAI, Anthropic, Google Generative AI SDKs
- **Deployment**: Docker, Streamlit Sharing, or cloud platforms

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

Please make sure your code adheres to our style guidelines and includes appropriate tests.

## Support

If you encounter any issues or have questions:

1. Check the existing issues in the repository
2. Submit a new issue with detailed information about the problem
3. Provide steps to reproduce the issue
4. Include information about your environment (OS, Python version, etc.)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Streamlit team for the excellent framework
- Contributors of the open-source libraries used in this project
- The data science community for sharing knowledge and best practices

---

Made with ❤️ and Streamlit
