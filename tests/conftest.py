"""
FINESE2 - Pytest Configuration and Fixtures
"""
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    import pandas as pd
    import numpy as np
    
    return pd.DataFrame({
        'id': range(1, 101),
        'name': [f'User_{i}' for i in range(1, 101)],
        'age': np.random.randint(18, 70, 100),
        'salary': np.random.uniform(30000, 100000, 100),
        'department': np.random.choice(['Engineering', 'Sales', 'Marketing', 'HR'], 100)
    })
