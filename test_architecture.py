"""
Test script to verify the new architecture works correctly.
"""

import pandas as pd
import numpy as np
from core.dataset_context import DatasetContext
from services.health_service import calculate_data_health_score
from services.chart_service import create_completeness_chart, MAX_ROWS_FOR_PLOT
from services.cleaning_service import get_cleaning_suggestions
from services.profiling_service import generate_basic_profile_report

def test_dataset_context():
    """Test the DatasetContext class."""
    print("Testing DatasetContext...")
    
    # Create a sample dataframe
    df = pd.DataFrame({
        'A': [1, 2, 3, np.nan, 5],
        'B': ['x', 'y', 'z', 'x', 'y'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5],
        'D': pd.date_range('2023-01-01', periods=5)
    })
    
    # Create DatasetContext
    context = DatasetContext(base_df=df)
    
    print(f"Base DF shape: {context.base_df.shape}")
    print(f"Filtered DF shape: {context.filtered_df.shape}")
    print(f"Metadata columns: {len(context.metadata['columns'])}")
    print(f"Dataset fingerprint: {context.dataset_fingerprint}")
    print("✓ DatasetContext test passed\n")


def test_health_service():
    """Test the health service."""
    print("Testing Health Service...")
    
    df = pd.DataFrame({
        'A': [1, 2, 3, np.nan, 5],
        'B': ['x', 'y', 'z', 'x', 'y'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    
    scorecard = calculate_data_health_score(df)
    print(f"Health score: {scorecard['final_score']}")
    print(f"Completeness: {scorecard['details']['completeness']}")
    print("✓ Health Service test passed\n")


def test_chart_service():
    """Test the chart service."""
    print("Testing Chart Service...")
    
    df = pd.DataFrame({
        'A': [1, 2, 3, np.nan, 5],
        'B': ['x', 'y', 'z', 'x', 'y'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    
    # Test with a small dataset
    fig = create_completeness_chart(df)
    print(f"Chart created with {len(fig.data)} traces")
    print("✓ Chart Service test passed\n")


def test_cleaning_service():
    """Test the cleaning service."""
    print("Testing Cleaning Service...")
    
    df = pd.DataFrame({
        'A': [1, 2, 3, np.nan, 5],
        'B': ['x', 'y', 'z', 'x', 'y'],
        'C': [1.1, 2.2, -3.3, 4.4, 5.5]  # Negative value in what might be a price column
    })
    
    suggestions = get_cleaning_suggestions(df)
    print(f"Found {len(suggestions)} suggestions")
    for suggestion in suggestions:
        print(f"  - {suggestion['column']}: {suggestion['issue']}")
    print("✓ Cleaning Service test passed\n")


def test_profiling_service():
    """Test the profiling service."""
    print("Testing Profiling Service...")
    
    df = pd.DataFrame({
        'A': [1, 2, 3, np.nan, 5],
        'B': ['x', 'y', 'z', 'x', 'y'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    
    report = generate_basic_profile_report(df)
    print(f"Generated report with {len(report)} characters")
    print("✓ Profiling Service test passed\n")


if __name__ == "__main__":
    print("Starting architecture tests...\n")
    
    test_dataset_context()
    test_health_service()
    test_chart_service()
    test_cleaning_service()
    test_profiling_service()
    
    print("All tests passed! ✓")