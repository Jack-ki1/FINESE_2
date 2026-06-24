# Contributing to FINESE2

Thank you for your interest in contributing to FINESE2! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

## Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of the repository page.

### 2. Clone Your Fork

```bash
git clone https://github.com/your-username/FINESE2.git
cd FINESE2
```

### 3. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

## Development Workflow

### 1. Make Your Changes

- Write clean, readable code
- Follow existing code patterns
- Add comments where necessary
- Update documentation if needed

### 2. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Check code formatting
black --check app/ tests/
isort --check-only app/ tests/

# Run linters
flake8 app/ tests/
```

### 3. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

**Commit Message Format:**
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for code style changes
- `refactor:` for code refactoring
- `test:` for adding/updating tests
- `chore:` for maintenance tasks

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create a Pull Request

Go to the original repository and click "New Pull Request".

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these specifics:

- **Line length**: 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Organized with isort
- **Formatting**: Black formatter
- **Type hints**: Use where applicable

### Example Code Style

```python
from typing import Dict, List, Optional
import pandas as pd


class DataLoader:
    """Load and validate data from various sources."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data: Optional[pd.DataFrame] = None
    
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Loaded DataFrame
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not filepath.endswith('.csv'):
            raise ValueError("File must be CSV format")
        
        self.data = pd.read_csv(filepath)
        return self.data
```

### Naming Conventions

- **Variables/functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Private methods**: _leading_underscore

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files: `test_<module>.py`
- Name test classes: `Test<ClassName>`
- Name test functions: `test_<functionality>`

### Test Example

```python
import pytest
from app.core.data import DataManager


class TestDataManager:
    """Tests for DataManager."""
    
    def test_load_sample_dataset(self):
        """Test loading sample dataset."""
        manager = DataManager()
        df = manager.load_sample_dataset('iris')
        
        assert df is not None
        assert len(df) == 150
        assert 'species' in df.columns
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_data.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Documentation

### Updating Documentation

- Update relevant `.md` files in `docs/`
- Add docstrings to new functions/classes
- Update README.md if needed
- Include examples where helpful

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When condition occurs
    """
    pass
```

## Submitting Changes

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

## Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linters
2. **Code Review**: At least one maintainer reviews your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged
5. **Cleanup**: Delete your branch after merging

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an Issue
- **Chat**: Join our Discord/Slack (if available)

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Special mentions for significant contributions

---

Thank you for contributing to FINESE2! 🎉
