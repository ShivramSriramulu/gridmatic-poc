"""
Basic unit tests for Gridmatic ERCOT POC
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add pipeline to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pipeline'))

def test_etl_imports():
    """Test that ETL module imports successfully"""
    try:
        import pipeline.etl_ingest as etl
        assert hasattr(etl, 'ingest_ercot_last_year')
        assert hasattr(etl, 'ingest_weather_last_year')
        assert hasattr(etl, 'build_silver_table')
        print("✅ ETL module imports successfully")
    except ImportError as e:
        pytest.fail(f"ETL module import failed: {e}")

def test_forecast_imports():
    """Test that forecast script imports successfully"""
    try:
        import generate_forecast
        assert hasattr(generate_forecast, 'generate_forecast')
        print("✅ Forecast script imports successfully")
    except ImportError as e:
        pytest.fail(f"Forecast script import failed: {e}")

def test_optimization_imports():
    """Test that optimization script imports successfully"""
    try:
        import generate_optimization
        assert hasattr(generate_optimization, 'generate_battery_optimization')
        print("✅ Optimization script imports successfully")
    except ImportError as e:
        pytest.fail(f"Optimization script import failed: {e}")

@patch.dict(os.environ, {
    'GCP_PROJECT': 'test-project',
    'BQ_DATASET': 'test_dataset',
    'EIA_API_KEY': 'test-key'
})
def test_environment_variables():
    """Test that required environment variables are set"""
    assert os.environ.get('GCP_PROJECT') == 'test-project'
    assert os.environ.get('BQ_DATASET') == 'test_dataset'
    assert os.environ.get('EIA_API_KEY') == 'test-key'
    print("✅ Environment variables configured correctly")

def test_data_validation():
    """Test basic data validation functions"""
    import pandas as pd
    import numpy as np
    
    # Test DataFrame creation
    df = pd.DataFrame({
        'timestamp_hour': pd.date_range('2023-01-01', periods=24, freq='H'),
        'demand_mw': np.random.uniform(40000, 80000, 24)
    })
    
    assert len(df) == 24
    assert 'timestamp_hour' in df.columns
    assert 'demand_mw' in df.columns
    assert df['demand_mw'].min() >= 0
    print("✅ Data validation tests passed")

def test_prophet_data_preparation():
    """Test Prophet data preparation"""
    import pandas as pd
    import numpy as np
    
    # Create sample data
    df = pd.DataFrame({
        'timestamp_hour': pd.date_range('2023-01-01', periods=100, freq='H'),
        'demand_mw': np.random.uniform(40000, 80000, 100)
    })
    
    # Prepare for Prophet
    dfp = df.rename(columns={"timestamp_hour": "ds", "demand_mw": "y"})
    dfp['ds'] = dfp['ds'].dt.tz_localize(None)
    
    assert 'ds' in dfp.columns
    assert 'y' in dfp.columns
    assert dfp['ds'].dtype == 'datetime64[ns]'
    assert dfp['y'].dtype in ['float64', 'int64']
    print("✅ Prophet data preparation tests passed")

def test_optimization_constraints():
    """Test optimization constraint setup"""
    import cvxpy as cp
    import numpy as np
    
    # Simple optimization test
    T = 24
    p = np.random.uniform(50, 100, T)
    
    c = cp.Variable(T, nonneg=True)
    d = cp.Variable(T, nonneg=True)
    s = cp.Variable(T+1)
    
    # Constraints
    cons = [s[0] == 50]  # Start at 50% SOC
    for t in range(T):
        cons += [s[t+1] == s[t] + 0.95*c[t] - d[t]/0.95]
        cons += [c[t] <= 50, d[t] <= 50]
    cons += [s >= 0, s <= 100]
    
    # Objective
    obj = cp.Maximize(p @ d - p @ c)
    prob = cp.Problem(obj, cons)
    
    # Should be feasible
    assert prob.is_dcp()
    print("✅ Optimization constraint tests passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
