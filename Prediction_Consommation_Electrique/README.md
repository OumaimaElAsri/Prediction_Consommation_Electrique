# Energy Consumption Prediction - France

Simple machine learning project to predict electricity consumption based on weather and energy data.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
python predict.py
```

## Project Structure

- `main.py` - Main pipeline
- `predict.py` - Predictions
- `run_demo.py` - Demo with test data
- `scripts/` - Core modules
- `data/` - Input data (meteorological, RTE energy)
- `notebooks/` - Jupyter analysis
- `output/` - Results

## What It Does

1. Loads meteorological data from 15 French departments
2. Merges with RTE energy mix data
3. Creates 25+ features (temporal, lag, rolling stats)
4. Trains XGBoost model with time-series validation
5. Generates predictions with error metrics

## Data

- **Meteorological**: Temperature, humidity, wind, pressure (15 departments)
- **RTE**: Energy mix breakdown (renewable, nuclear, fossil)
- **Output**: Merged dataset with predictions

## Requirements

Python 3.11+ with pandas, numpy, xgboost, scikit-learn, plotly, jupyter

See `requirements.txt` for full list.

## Configuration

Edit `scripts/config.py` to customize data paths, interpolation methods, model parameters.

## Output

- `output/dataset_final_clean.csv` - Main dataset
- `output/predictions.csv` - Model predictions

