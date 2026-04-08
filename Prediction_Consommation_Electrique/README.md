# 🔋 Prediction Consommation Électrique

Prédiction de la consommation électrique en France basée sur données météorologiques et énergétiques RTE.

## 📊 Project Overview

This project predicts electricity consumption for 15 French departments using:
- **Meteorological data** (temperature, humidity, wind, etc.)
- **RTE energy mix data** (renewable, nuclear, etc.)
- **XGBoost model** with time-series validation

## 🚀 Quick Start

### 1. Environment Setup
```bash
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

### 2. Run Pipeline
```bash
python main.py
```

### 3. Launch Dashboard
```bash
streamlit run streamlit_dashboard.py
```

### 4. Run Demo (with smaller dataset)
```bash
python run_demo.py
```

## 📁 Project Structure

```
Prediction_Consommation_Electrique/
├── main.py                    # Main pipeline execution
├── predict.py                 # Prediction module
├── run_demo.py                # Demo execution script
├── streamlit_dashboard.py     # Interactive dashboard
├── requirements.txt           # Python dependencies
├── scripts/                   # Core modules
│   ├── config.py              # Configuration presets
│   ├── data_pipeline.py       # Data processing pipeline
│   ├── data_cleaning.py       # Data cleaning functions
│   ├── feature_engineering.py # Feature creation
│   ├── modeling.py            # Model training
│   └── utils.py               # Utility functions
├── data/                      # Data directory
│   ├── Data_Climat/           # Meteorological data (15 depts)
│   ├── Data_eCO2/             # RTE energy data
│   └── Departements/          # GeoJSON department boundaries
├── notebooks/                 # Jupyter notebooks
│   ├── 01_Data_Cleaning_Preprocessing.ipynb
│   └── 02_Pipeline_Complete_Meteo_RTE.ipynb
└── output/                    # Generated output files
```

## 🎯 Key Features

- **15 French Departments**: H_06, H_13, H_31, H_33, H_34, H_35, H_42, H_44, H_51, H_59, H_67, H_69, H_75, H_76, H_83
- **25+ Engineered Features**: Temporal, lag, rolling statistics, meteorological transformations
- **Time-Series Validation**: Proper temporal split to avoid data leakage
- **Interactive Dashboard**: 4-page Streamlit app with maps, charts, and predictions
- **Memory Optimized**: Lazy loading and caching for large datasets

## 💻 Dashboard Pages

1. **Home** - Project overview and key metrics
2. **Data Quality** - Data cleaning indicators and validation
3. **EDA** - Exploratory Data Analysis with maps and correlations
4. **Predictions** - Real vs Predicted consumption with error metrics (MAE, RMSE)

## 📊 Model Performance

- **Algorithm**: XGBoost with hyperparameter tuning
- **Validation**: Time-series k-fold cross-validation
- **Features**: 25+ engineered features from meteorological and energy data
- **Output**: Detailed predictions with confidence intervals

## 🔧 Configuration

Edit `scripts/config.py` for pipeline customization:
- Data paths
- Interpolation methods
- Outlier detection thresholds
- Model hyperparameters

## 📚 Usage Examples

```python
from scripts.data_pipeline import EnergyDataPipeline
from pathlib import Path

pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)

df = pipeline.run(save_intermediate=True)
```

## 🎓 Technologies

- **Python 3.11+**
- **Pandas 2.1.0+** - Data manipulation
- **XGBoost 2.0+** - Machine learning
- **Streamlit 1.28+** - Interactive dashboard
- **Plotly 5.17+** - Interactive visualizations
- **Folium 0.14+** - Map visualizations

## 📝 Requirements

See `requirements.txt` for full dependency list:
```
pandas>=2.1.0
numpy>=1.26.0
xgboost>=2.0
scikit-learn>=1.3
streamlit>=1.28
plotly>=5.17
folium>=0.14
streamlit-folium
jupyter
```

## 🔄 Pipeline Steps

1. **Load** - Read meteorological and RTE data
2. **Clean** - Handle missing values and outliers
3. **Fuse** - Merge datasets by date and department
4. **Engineer** - Create 25+ features
5. **Validate** - Quality checks and transformations
6. **Train** - XGBoost model with cross-validation
7. **Predict** - Generate consumption forecasts
8. **Visualize** - Interactive dashboard

## 📈 Deployment

### Local Development
```bash
streamlit run streamlit_dashboard.py
```

### Production
```bash
streamlit run streamlit_dashboard.py --logger.level=warning
```

For Docker/Cloud deployment, refer to deployment documentation in code comments.

## 📞 Contact & Support

For issues or questions, check the code comments and docstrings throughout the project.

## 📄 License

Private project

---

**Last Updated**: April 2026
**Status**: Production Ready ✅
