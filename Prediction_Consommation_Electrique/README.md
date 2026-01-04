# Prédiction de la Consommation Électrique Régionale en France 🔌⚡

**Pipeline End-to-End pour la fusion et l'analyse de données énergétiques**

## 🎯 Objectif

Développer un système robuste et modulaire pour :
- Fusionner les données météorologiques (CSV horaires par département)
- Fusionner les données RTE eCO2mix (Excel)
- Nettoyer et valider la qualité des données
- Préparer les données pour la modélisation prédictive

## 📁 Structure du Projet

```
Prediction_Consommation_Electrique/
├── data/
│   ├── Data_Climat/           # CSV météo (H_75_latest.csv, etc.)
│   └── Data_eCO2/             # Excel RTE (eCO2mix_RTE_*.xls)
├── scripts/                   # Pipeline modulaire
│   ├── __init__.py
│   ├── data_pipeline.py       # 🔴 PIPELINE PRINCIPAL (6 classes)
│   ├── data_cleaning.py       # Nettoyage basique
│   ├── data_preprocessing.py  # Prétraitement
│   ├── config.py              # Configuration centralisée
│   ├── utils.py               # Utilitaires
│   └── test_data_pipeline.py  # Tests unitaires (pytest)
├── notebooks/
│   ├── 01_Data_Cleaning_Preprocessing.ipynb
│   └── 02_Pipeline_Complete_Meteo_RTE.ipynb
├── output/                    # Résultats (CSV, Parquet)
├── logs/                      # Fichiers de log
├── requirements.txt
└── README.md
```

## 🏗️ Architecture du Pipeline

### 1. **MeteoDataPipeline** 📊
```python
from scripts.data_pipeline import MeteoDataPipeline

pipeline = MeteoDataPipeline(Path("data/Data_Climat"))
df_meteo = pipeline.load_and_clean_meteo()
```

**Fonctionnalités:**
- Scan de tous les fichiers CSV avec pattern `H_XX_*.csv`
- Extraction du code département via **regex** : `H_(\d{2,3})_`
- Ajout automatique de colonne `code_dept` à chaque DataFrame
- Fusion de tous les fichiers en un unique DataFrame
- Nettoyage des noms de colonnes

### 2. **RTEDataPipeline** 📈
```python
from scripts.data_pipeline import RTEDataPipeline

pipeline = RTEDataPipeline(Path("data/Data_eCO2"), skiprows=3)
df_rte = pipeline.load_and_clean_rte()
```

**Fonctionnalités:**
- Lecture des fichiers Excel avec gestion des **métadonnées**
- Saut des premières lignes (RTE ajoute souvent des infos en haut)
- Identification automatique des colonnes dates
- Conversion en `datetime`
- Fusion de tous les fichiers

### 3. **DataFusionPipeline** 🔗
```python
from scripts.data_pipeline import DataFusionPipeline

df_final = DataFusionPipeline.merge_datasets(
    df_meteo, df_rte,
    meteo_date_col='date',
    rte_date_col='date',
    how='inner'
)
```

**Fonctionnalités:**
- Fusion temporelle sur les colonnes de date
- Support des jointures : `inner`, `outer`, `left`, `right`
- Conversion automatique de dates en `datetime`
- Suppression des colonnes dupliquées

### 4. **DataQualityPipeline** ✨
```python
from scripts.data_pipeline import DataQualityPipeline

df_clean = DataQualityPipeline.handle_missing_values(
    df_final,
    numeric_interpolation='linear',
    categorical_fill='forward'
)
```

**Fonctionnalités:**
- **Interpolation linéaire** (limitée à 4 points) pour données numériques
  - Préserve les tendances naturelles
  - Évite l'extrapolation excessive
- **Forward fill** pour catégories
  - Maintient la dernière valeur stable
- Détection des outliers via **IQR**

### 5. **EnergyDataPipeline** 🚀
Orchestrateur principal qui chaîne tous les pipelines ci-dessus.

```python
from scripts.data_pipeline import EnergyDataPipeline

pipeline = EnergyDataPipeline(
    meteo_path="data/Data_Climat",
    rte_path="data/Data_eCO2",
    output_path="output"
)

df_final = pipeline.run(
    meteo_date_col='date',
    rte_date_col='date',
    save_intermediate=True
)
```

## ⚙️ Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Optionnel: pytest pour les tests
pip install pytest
```

## 🚀 Quick Start

### Approche 1: Pipeline Complet (Recommandé)
```python
from pathlib import Path
from scripts.data_pipeline import EnergyDataPipeline

pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)

# Exécute tout : load → clean → merge → validate
df_clean = pipeline.run(save_intermediate=True)
```

### Approche 2: Étapes Individuelles
```python
from scripts.data_pipeline import MeteoDataPipeline, RTEDataPipeline, DataFusionPipeline

# Étape 1
meteo = MeteoDataPipeline(Path("data/Data_Climat"))
df_meteo = meteo.load_and_clean_meteo()

# Étape 2
rte = RTEDataPipeline(Path("data/Data_eCO2"))
df_rte = rte.load_and_clean_rte()

# Étape 3
df_merged = DataFusionPipeline.merge_datasets(df_meteo, df_rte)
```

### Approche 3: Configuration Personnalisée
```python
from scripts.config import ConfigPresets, PipelineConfig
from scripts.data_pipeline import EnergyDataPipeline

# Charger une configuration prédéfinie
config = ConfigPresets.production()

# Ou créer une configuration personnalisée
custom_config = PipelineConfig()
custom_config.quality.numeric_interpolation = 'polynomial'
custom_config.quality.iqr_multiplier = 2.0
```

## 📊 Gestion des Données Manquantes

### Stratégie d'Interpolation Choisie: **Linear**

**Rationale:**
- ✅ Données énergétiques = continuité temporelle
- ✅ Préserve les tendances et gradients
- ✅ Adapté aux séries temporelles avec peu de gaps
- ✅ Rapide computationnellement

**Alternative: Polynomial**
- Utilisée si gaps > 4h avec tendances complexes
- Plus robuste mais coûteux en calcul

**Limite d'interpolation: 4 points max**
- Évite l'extrapolation sur les gaps longs
- Pour gaps > 4h : la valeur reste NaN

## 🧪 Tests Unitaires

```bash
# Exécuter tous les tests
pytest scripts/test_data_pipeline.py -v

# Exécuter un test spécifique
pytest scripts/test_data_pipeline.py::TestMeteoDataPipeline::test_extract_dept_code_valid -v

# Avec rapport de couverture
pytest scripts/test_data_pipeline.py --cov=scripts --cov-report=html
```

**Classes de test:**
- `TestMeteoDataPipeline` - Extraction codes dept, chargement CSV
- `TestRTEDataPipeline` - Identification colonnes dates, Excel
- `TestDataFusionPipeline` - Jointures, conversion dates
- `TestDataQualityPipeline` - Interpolation, outliers
- `TestDataIntegration` - Pipeline complet

## 📝 Configuration

Fichier: `scripts/config.py`

```python
# Configuration par défaut
from scripts.config import DEFAULT_CONFIG

# Configuration development
from scripts.config import ConfigPresets
dev_config = ConfigPresets.development()

# Configuration production
prod_config = ConfigPresets.production()
```

**Éléments configurables:**
- Chemins des sources
- Delimiteurs CSV / sheets Excel
- Méthodes d'interpolation
- Seuils outliers (IQR, Z-score)
- Format de sortie (CSV, Parquet)

## 📈 Outputs

Le pipeline génère 4 fichiers dans `/output/`:

```
output/
├── 01_meteo_raw.csv         # Données météo brutes fusionnées
├── 02_rte_raw.csv           # Données RTE brutes fusionnées
├── 03_merged_raw.csv        # Fusion avant nettoyage
├── 04_data_final.csv        # Final ✅
└── dataset_final_clean.parquet
```

## 🔍 Logging

Tous les événements sont loggés :
```
INFO - Pipeline météo initialisé avec le chemin: data/Data_Climat
INFO - Trouvé 96 fichier(s) CSV
INFO - Traitement du fichier: H_75_latest-2025-2026.csv
INFO - ✓ Fichier chargé: 8760 lignes, 5 colonnes
...
```

## 🛠️ Utilities

**scripts/utils.py**
- `get_project_paths()` - Chemins du projet
- `create_data_summary()` - Statistiques descriptives
- `save_data()` - Sauvegarder DataFrame
- `load_data()` - Charger DataFrame

## 📚 Notebooks

### 01_Data_Cleaning_Preprocessing.ipynb
Nettoyer + prétraiter des données

### 02_Pipeline_Complete_Meteo_RTE.ipynb
Exécuter le pipeline complet avec visualisations

## ✨ Points Techniques

✅ **pathlib** pour gestion moderne des chemins
✅ **Type hinting** sur toutes les fonctions
✅ **Logging structuré** pour traçabilité
✅ **Regex** pour extraction robuste
✅ **Pandas datetime** pour alignement temporel
✅ **Tests unitaires** avec pytest
✅ **Configuration centralisée** (config.py)
✅ **Code documenté** avec docstrings
✅ **Gestion d'erreurs** complète

## 🎓 Utilisation dans un Notebook

```python
from pathlib import Path
from scripts.data_pipeline import EnergyDataPipeline

# Initialiser
pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)

# Exécuter
df = pipeline.run(save_intermediate=True)

# Explorer
print(df.shape)
print(df.columns)
print(df.describe())
```

## 📧 Support

Pour questions ou bugs, consultez les tests unitaires comme exemples d'utilisation.
