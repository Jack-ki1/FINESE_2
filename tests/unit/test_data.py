"""Tests for data management module."""
import pytest
from app.core.data import DataManager


class TestDataManager:
    """Test suite for DataManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.data_manager = DataManager()
    
    def test_load_sample_dataset_iris(self):
        """Test loading iris sample dataset."""
        df = self.data_manager.load_sample_dataset('iris')
        assert df is not None
        assert len(df) == 150
        assert 'species' in df.columns
    
    def test_load_sample_dataset_titanic(self):
        """Test loading titanic sample dataset."""
        df = self.data_manager.load_sample_dataset('titanic')
        assert df is not None
        assert len(df) == 1000
        assert 'survived' in df.columns
    
    def test_load_sample_dataset_wine(self):
        """Test loading wine sample dataset."""
        df = self.data_manager.load_sample_dataset('wine')
        assert df is not None
        assert len(df) == 178
        assert 'class' in df.columns
    
    def test_load_invalid_sample_dataset(self):
        """Test loading invalid sample dataset raises error."""
        with pytest.raises(ValueError):
            self.data_manager.load_sample_dataset('invalid_dataset')
