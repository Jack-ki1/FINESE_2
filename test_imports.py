"""
Simple test to verify imports work correctly
"""

def test_imports():
    try:
        # Test importing the core components
        from core.dataset_context import DatasetContext
        print("✓ DatasetContext imported successfully")
        
        # Test importing services
        from services.health_service import calculate_data_health_score
        print("✓ Health service imported successfully")
        
        from services.chart_service import create_completeness_chart
        print("✓ Chart service imported successfully")
        
        from services.cleaning_service import get_cleaning_suggestions
        print("✓ Cleaning service imported successfully")
        
        from services.profiling_service import generate_basic_profile_report
        print("✓ Profiling service imported successfully")
        
        # Test importing utilities
        from utils.data_utils import is_numeric_column, is_categorical_column, is_datetime_column
        print("✓ Data utils imported successfully")
        
        # Test importing the main modules in app.py
        import logging
        from logging_config import setup_logging
        print("✓ Logging config imported successfully")
        
        print("\nAll imports successful! ✓")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()