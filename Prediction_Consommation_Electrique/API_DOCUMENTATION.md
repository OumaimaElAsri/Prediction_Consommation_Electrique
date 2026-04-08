# API Documentation - Energy Prediction Pipeline

## 📖 Core Modules

### data_pipeline.py

#### EnergyDataPipeline
Main orchestration class for the complete pipeline.

```python
pipeline = EnergyDataPipeline(
    meteo_path: Path,
    rte_path: Path,
    output_path: Path
)

# Run full pipeline
df = pipeline.run(save_intermediate=True)
```

**Methods:**
- `run(save_intermediate=True)` - Execute complete pipeline

---

#### MeteoDataPipeline
Handles meteorological data processing.

```python
meteo = MeteoDataPipeline(data_path)
df = meteo.load_and_clean_meteo()
```

**Methods:**
- `load_and_clean_meteo()` - Load and clean all meteorological files

---

#### RTEDataPipeline
Handles RTE energy mix data.

```python
rte = RTEDataPipeline(data_path, skiprows=3)
df = rte.load_and_clean_rte()
```

**Methods:**
- `load_and_clean_rte()` - Load and clean RTE data

---

#### DataFusionPipeline
Merges meteorological and RTE datasets.

```python
df_merged = DataFusionPipeline.merge_datasets(
    df_meteo,
    df_rte,
    meteo_date_col='date',
    rte_date_col='date',
    how='inner'
)
```

**Static Methods:**
- `merge_datasets()` - Merge two DataFrames on date

---

#### DataQualityPipeline
Data validation and cleaning.

```python
df_clean = DataQualityPipeline.handle_missing_values(
    df,
    numeric_interpolation='linear',
    categorical_fill='forward'
)

outliers = DataQualityPipeline.detect_and_report_outliers(df)
```

**Static Methods:**
- `handle_missing_values()` - Interpolation and filling
- `detect_and_report_outliers()` - IQR-based outlier detection

---

### feature_engineering.py

#### FeatureEngineer
Creates 25+ features from raw data.

```python
engineer = FeatureEngineer(df)
df_features = engineer.create_all_features()
```

**Features Created:**
- **Temporal**: Hour, day_of_week, month, season, day_of_year
- **Lag**: Previous 1, 3, 6, 24, 168 hour values
- **Rolling**: 3, 6, 24 hour rolling means/stds
- **Meteorological**: Temperature transformations, interactions
- **Fourier**: Seasonal decomposition features

---

### modeling.py

#### EnergyModel
XGBoost model for predictions.

```python
model = EnergyModel()
model.train(X_train, y_train)
predictions = model.predict(X_test)
metrics = model.evaluate(y_test, predictions)
```

**Methods:**
- `train(X, y)` - Train XGBoost model
- `predict(X)` - Make predictions
- `evaluate(y_true, y_pred)` - Calculate metrics

---

### config.py

#### ConfigPresets
Predefined configurations.

```python
config = ConfigPresets.production()
config = ConfigPresets.development()
```

#### PipelineConfig
Customizable configuration object.

```python
config = PipelineConfig()
config.quality.numeric_interpolation = 'polynomial'
config.quality.iqr_multiplier = 2.0
```

---

## 🎯 Main Scripts

### main.py
Execute full pipeline end-to-end.

```bash
python main.py
```

**Output:**
- Cleaned and merged dataset to `output/`

---

### predict.py
Generate predictions using trained model.

```bash
python predict.py
```

**Output:**
- Predictions CSV with confidence intervals

---

### run_demo.py
Run pipeline with test data (memory-efficient).

```bash
python run_demo.py --keep-demo-data
```

**Output:**
- Demo predictions in `demo_data/`

---

### streamlit_dashboard.py
Interactive dashboard for visualization.

```bash
streamlit run streamlit_dashboard.py
```

**Pages:**
1. **Accueil** (Home) - Project overview, metrics
2. **Qualité des Données** (Data Quality) - Data cleaning stats
3. **Analyse Exploratoire** (EDA) - Maps, correlations, distributions
4. **Prédictions** (Predictions) - Forecast visualization, error analysis

---

## 📊 Data Schema

### Meteorological Data
```
date: AAAAMMJJHH format (year-month-day-hour)
code_dept: Department code (e.g., '75')
temperature: Temperature in °C
humidity: Humidity %
wind_speed: Wind speed
pressure: Atmospheric pressure
precipitation: Precipitation mm
```

### RTE Data
```
date: Daily date
renewable: Renewable energy %
nuclear: Nuclear energy %
fossil: Fossil fuel %
other: Other sources %
```

### Merged Output
```
date: Datetime
code_dept: Department code
[All meteorological columns]
[All RTE columns]
[25+ Engineered features]
```

---

## 🔧 Configuration Parameters

### Quality Settings
```python
config.quality.numeric_interpolation = 'linear' | 'polynomial' | 'spline'
config.quality.interpolation_limit = 5  # Max consecutive interpolation
config.quality.categorical_fill = 'forward' | 'backward' | 'mean'
config.quality.iqr_multiplier = 1.5  # Outlier threshold
```

### Model Settings
```python
config.model.n_estimators = 200
config.model.max_depth = 8
config.model.learning_rate = 0.05
config.model.subsample = 0.8
```

---

## 📈 Performance Metrics

- **MAE** - Mean Absolute Error
- **RMSE** - Root Mean Squared Error
- **MAPE** - Mean Absolute Percentage Error
- **R²** - Coefficient of Determination

---

## ⚠️ Error Handling

All modules include logging and error handling:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing data...")
logger.warning("Missing data detected")
logger.error("Pipeline failed")
```

---

## 💾 File I/O

### Input Data
```
data/
├── Data_Climat/
│   └── H_*.csv  (15 department files)
├── Data_eCO2/
│   └── eCO2mix_RTE_tempo_*.csv
└── Departements/
    └── departements.geojson
```

### Output Files
```
output/
├── features_engineered.csv
├── predictions.csv
└── model_metadata.json
```

---

## 🚀 Quick Integration Example

```python
from pathlib import Path
from scripts.data_pipeline import EnergyDataPipeline
from scripts.modeling import EnergyModel

# Step 1: Prepare data
pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)
df = pipeline.run()

# Step 2: Train model
model = EnergyModel()
X = df.drop('consumption', axis=1)
y = df['consumption']
model.train(X, y)

# Step 3: Predict
predictions = model.predict(X)
```

---

**API Version**: 1.0  
**Last Updated**: April 2026
