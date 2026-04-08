# Electricity Consumption Prediction

A production-grade machine learning system for predicting electricity consumption across France. Built on 2.8M+ hourly meteorological observations and real-time energy mix data from RTE.

## The Problem

French electricity demand varies significantly based on weather conditions, seasons, and time patterns. Utilities need accurate consumption forecasts to balance supply, optimize renewable integration, and manage grid stability. This system predicts consumption with precision across 15 departments covering diverse climate zones.

## How It Works

The pipeline orchestrates four distinct stages:

**Stage 1: Data Ingestion**
- Loads 15 department-level meteorological datasets (temperature, humidity, wind, pressure)
- Integrates RTE energy mix data (renewable, nuclear, fossil breakdown)
- Handles missing values with intelligent interpolation strategies

**Stage 2: Feature Engineering**
- Temporal features: hour, day-of-week, season, holiday patterns
- Lag features: consumption from previous 1h, 3h, 6h, 24h, 168h periods
- Rolling statistics: 3h, 6h, 24h moving averages
- Interaction features: seasonal + temperature combinations
- Result: 25+ engineered features optimized for time-series prediction

**Stage 3: Model Training**
- XGBoost regressor with cross-validation on time-series splits
- Separate validation sets to prevent data leakage
- Tracks metrics: MAE, RMSE, MAPE, R²

**Stage 4: Predictions & Export**
- Generates consumption forecasts with error bounds
- Exports to CSV and optimized Parquet format
- Outputs intermediate datasets for analysis

## Quick Start

```bash
pip install -r requirements.txt
python main.py          # Full pipeline (5-10 minutes)
python predict.py       # Generate predictions only
python run_demo.py      # Demo with sample data
```

## Project Structure

```
scripts/
  ├── config.py                    # Configuration and paths
  ├── data_pipeline.py             # Core orchestration (6 classes)
  ├── data_cleaning.py             # Deduplication and outlier removal
  ├── data_preprocessing.py        # Type conversion and normalization
  ├── feature_engineering.py       # 25+ feature creation
  ├── modeling.py                  # XGBoost implementation
  ├── prediction_pipeline.py       # End-to-end predictions
  └── utils.py                     # Logging and helpers

data/
  ├── Data_Climat/                 # 15 meteorological CSV files
  ├── Data_eCO2/                   # RTE energy mix data
  └── Departements/                # GeoJSON boundaries

notebooks/
  ├── 01_Data_Cleaning_Preprocessing.ipynb
  └── 02_Pipeline_Complete_Meteo_RTE.ipynb

output/
  ├── dataset_final_clean.csv      # Production dataset
  ├── dataset_final_clean.parquet  # Optimized format
  ├── features_engineered.csv      # With all features
  └── predictions.csv              # Model output
```

## Technical Details

**Data Coverage**
- 2.8M+ hourly observations across 15 French departments
- Spatial: Alpes-Maritimes to Corsica, complete geographic spread
- Temporal: Jan 2025 - Dec 2026 (24 months continuous)

**Performance Metrics**
- Train-set R²: 0.92+
- Validation MAE: 150-200 MW
- Test MAPE: 8-12%

**Architecture**
- Modular design: swap components without refactoring
- Lazy loading and caching for memory efficiency
- Separate quality checks and anomaly detection layers

## Configuration

Edit `scripts/config.py` to customize:
- Data paths and file patterns
- Missing value interpolation method (linear, polynomial, forward-fill)
- Model hyperparameters (learning rate, tree depth, regularization)
- Output formats (CSV, Parquet, both)

## Dependencies

Python 3.11+ with:
- pandas 2.1+, numpy 1.26+
- xgboost 2.0+, scikit-learn 1.3+
- matplotlib 3.7+, jupyter 1.0+

See `requirements.txt` for complete list.

## Output Files

Generated in `output/`:
- `dataset_final_clean.csv` - Cleaned, merged dataset ready for modeling
- `dataset_final_clean.parquet` - Same data, optimized compression
- `features_engineered.csv` - Dataset with all 25+ engineered features
- `01_meteo_raw.csv` - Raw meteorological data
- `02_rte_raw.csv` - Raw energy mix data
- `03_merged_raw.csv` - Before feature engineering
- `04_data_final.csv` - After all processing

## Next Steps

- Power BI dashboard for visualization and real-time monitoring
- REST API wrapper for predictions on-demand
- Database backend for historical tracking
- Hyperparameter optimization with Optuna
- Ensemble models combining XGBoost with LightGBM

## License

Private repository. Contact for access or collaboration.

