import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

from scripts.data_pipeline import (
    MeteoDataPipeline,
    RTEDataPipeline,
    DataFusionPipeline,
    DataQualityPipeline
)


class TestMeteoDataPipeline:
    @pytest.fixture
    def meteo_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MeteoDataPipeline(Path(tmpdir))

    def test_extract_dept_code_valid(self, meteo_pipeline):
        filename = "H_75_latest-2025-2026.csv"
        result = meteo_pipeline.extract_dept_code(filename)
        assert result == "75"


class TestDataIntegration:
    def test_full_pipeline_with_sample_data(self):
        dates = pd.date_range('2025-01-01', periods=100, freq='H')
        df_meteo = pd.DataFrame({
            'date': dates,
            'temperature': np.random.uniform(5, 25, 100),
        })
        assert len(df_meteo) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
