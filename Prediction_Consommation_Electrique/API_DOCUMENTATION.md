# API Reference

## Core Classes

### EnergyDataPipeline
Main pipeline class for data processing.

```python
from scripts.data_pipeline import EnergyDataPipeline

pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)

df = pipeline.run(save_intermediate=True)
```

### MeteoDataPipeline
Load and clean meteorological data.

```python
from scripts.data_pipeline import MeteoDataPipeline

meteo = MeteoDataPipeline(Path("data/Data_Climat"))
df = meteo.load_and_clean_meteo()
```

### RTEDataPipeline
Load and clean RTE energy data.

```python
from scripts.data_pipeline import RTEDataPipeline

rte = RTEDataPipeline(Path("data/Data_eCO2"), skiprows=3)
df = rte.load_and_clean_rte()
```

### FeatureEngineer
Create predictive features from raw data.

```python
from scripts.feature_engineering import FeatureEngineer

engineer = FeatureEngineer(df)
df_features = engineer.create_all_features()
```

Features created:
- Temporal: hour, day_of_week, month, season
- Lag: previous 1, 3, 6, 24, 168 hours
- Rolling: 3, 6, 24 hour statistics
- Meteorological: transformations and interactions

### EnergyModel
XGBoost model for predictions.

```python
from scripts.modeling import EnergyModel

model = EnergyModel()
model.train(X_train, y_train)
predictions = model.predict(X_test)
metrics = model.evaluate(y_test, predictions)
```

## Main Scripts

### main.py
Execute complete pipeline.

```bash
python main.py
python main.py --config production
python main.py --output-format parquet
```

### predict.py
Generate predictions.

```bash
python predict.py
python predict.py --meteo-path data/Data_Climat
```

### run_demo.py
Demo with test data.

```bash
python run_demo.py
```

## Configuration

### ConfigPresets
Predefined configurations.

```python
from scripts.config import ConfigPresets

config = ConfigPresets.production()
config = ConfigPresets.development()
```

### PipelineConfig
Custom configuration.

```python
from scripts.config import PipelineConfig

config = PipelineConfig()
config.quality.numeric_interpolation = 'polynomial'
config.quality.iqr_multiplier = 2.0
```

## Data Formats

Input:
- Meteorological: CSV with dept code, date, temperature, humidity, etc.
- RTE: XLS with daily energy mix percentages

Output:
- CSV or Parquet with merged data + engineered features
- Predictions with error metrics (MAE, RMSE, MAPE, R²)

## Key Methods

`DataQualityPipeline`:
- `handle_missing_values()` - Interpolation and filling
- `detect_and_report_outliers()` - IQR-based detection

`DataFusionPipeline`:
- `merge_datasets()` - Merge on date columns

---

Last updated: April 2026

