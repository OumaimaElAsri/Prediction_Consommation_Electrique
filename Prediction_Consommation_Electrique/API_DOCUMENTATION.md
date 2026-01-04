# API Documentation - Pipeline Énergétique

## Vue d'ensemble

Le pipeline énergétique est composé de 6 classes principales organisées de manière modulaire :

```
MeteoDataPipeline ─┐
                   ├─→ DataFusionPipeline ─┐
RTEDataPipeline ───┘                       ├─→ DataQualityPipeline ─→ EnergyDataPipeline
                                            ↓
                                    (Orchestration complète)
```

---

## 1. MeteoDataPipeline

Classe pour charger et nettoyer les données météorologiques.

### Initialisation
```python
from pathlib import Path
from scripts.data_pipeline import MeteoDataPipeline

pipeline = MeteoDataPipeline(Path("data/Data_Climat"))
```

### Méthode: `extract_dept_code()`
Extrait le code département du nom de fichier via regex.

```python
code = pipeline.extract_dept_code("H_75_latest-2025-2026.csv")
# → "75"
```

**Paramètres:**
- `filename: str` - Nom du fichier

**Retour:**
- `str | None` - Code département (ex: "75") ou None

---

### Méthode: `load_and_clean_meteo()`
Charge tous les fichiers CSV, ajoute code_dept, et fusionne.

```python
df_meteo = pipeline.load_and_clean_meteo()
# Shape: (8760 * n_depts, n_colonnes+1)
```

**Paramètres:** Aucun

**Retour:**
- `pd.DataFrame` - DataFrame fusionné

**Colonnes ajoutées:**
- `code_dept` : Code département (extrait du nom de fichier)

**Exceptions:**
- `FileNotFoundError` - Répertoire n'existe pas
- `ValueError` - Aucun fichier CSV trouvé

---

## 2. RTEDataPipeline

Classe pour charger et nettoyer les données RTE (eCO2mix).

### Initialisation
```python
from scripts.data_pipeline import RTEDataPipeline

pipeline = RTEDataPipeline(
    Path("data/Data_eCO2"),
    skiprows=3  # Nombre de lignes de métadonnées à sauter
)
```

### Méthode: `load_and_clean_rte()`
Charge tous les fichiers Excel, gère les métadonnées, convertit les dates.

```python
df_rte = pipeline.load_and_clean_rte()
# Shape: (8760 * n_annees, n_colonnes)
```

**Paramètres:** Aucun

**Retour:**
- `pd.DataFrame` - DataFrame fusionné

**Conversion automatique:**
- Colonnes contenant 'date', 'heure', 'time', 'timestamp' → `datetime64`

**Exceptions:**
- `FileNotFoundError` - Répertoire n'existe pas
- `ValueError` - Aucun fichier Excel trouvé

---

### Méthode: `_identify_date_columns()` ⚠️ Private
Identifie les colonnes temporelles dans un DataFrame.

```python
date_cols = RTEDataPipeline._identify_date_columns(df)
# → ['date', 'timestamp']
```

---

## 3. DataFusionPipeline

Classe statique pour fusionner les données météo et RTE.

### Méthode: `merge_datasets()` (statique)
Fusionne deux DataFrames sur une clé temporelle.

```python
from scripts.data_pipeline import DataFusionPipeline

df_merged = DataFusionPipeline.merge_datasets(
    df_meteo,
    df_rte,
    meteo_date_col='date',
    rte_date_col='date',
    how='inner'
)
```

**Paramètres:**
- `df_meteo: pd.DataFrame` - DataFrame météo
- `df_rte: pd.DataFrame` - DataFrame RTE
- `meteo_date_col: str = 'date'` - Colonne de date en météo
- `rte_date_col: str = 'date'` - Colonne de date en RTE
- `how: str = 'inner'` - Type de jointure ('inner', 'outer', 'left', 'right')

**Retour:**
- `pd.DataFrame` - DataFrame fusionné

**Exceptions:**
- `ValueError` - Colonne de date n'existe pas

---

## 4. DataQualityPipeline

Classe statique pour améliorer la qualité des données.

### Méthode: `handle_missing_values()` (statique)
Gère les valeurs manquantes via interpolation et remplissage.

```python
from scripts.data_pipeline import DataQualityPipeline

df_clean = DataQualityPipeline.handle_missing_values(
    df_final,
    numeric_interpolation='linear',
    categorical_fill='forward'
)
```

**Paramètres:**
- `df: pd.DataFrame` - DataFrame à nettoyer
- `numeric_interpolation: str = 'linear'` - Méthode pour colonnes numériques
  - `'linear'` : Interpolation linéaire
  - `'polynomial'` : Interpolation polynomiale
  - `'time'` : Interpolation temporelle
- `categorical_fill: str = 'forward'` - Méthode pour catégories
  - `'forward'` : Forward fill (ffill)
  - `'backward'` : Backward fill (bfill)

**Retour:**
- `pd.DataFrame` - DataFrame nettoyé

**Stratégie:**
- Colonnes numériques : Interpolation linéaire (limite 4 points)
- Colonnes catégorielles : Forward + backward fill

---

### Méthode: `detect_and_report_outliers()` (statique)
Détecte les outliers via Interquartile Range (IQR).

```python
outliers = DataQualityPipeline.detect_and_report_outliers(
    df_clean,
    numeric_only=True
)
# → {'temperature': [45, 100, 234], 'consommation': [5031]}
```

**Paramètres:**
- `df: pd.DataFrame` - DataFrame à analyser
- `numeric_only: bool = True` - Analyser seulement colonnes numériques

**Retour:**
- `Dict[str, List[int]]` - {colonne: [indices outliers]}

**Formule IQR:**
- Borne inférieure: Q1 - 1.5 × IQR
- Borne supérieure: Q3 + 1.5 × IQR

---

## 5. EnergyDataPipeline

Orchestrateur principal qui chaîne tous les pipelines.

### Initialisation
```python
from scripts.data_pipeline import EnergyDataPipeline
from pathlib import Path

pipeline = EnergyDataPipeline(
    meteo_path=Path("data/Data_Climat"),
    rte_path=Path("data/Data_eCO2"),
    output_path=Path("output")
)
```

**Paramètres:**
- `meteo_path: Path` - Répertoire des données météo
- `rte_path: Path` - Répertoire des données RTE
- `output_path: Path | None = None` - Répertoire de sortie

---

### Méthode: `run()`
Exécute le pipeline complet.

```python
df_final = pipeline.run(
    meteo_date_col='date',
    rte_date_col='date',
    save_intermediate=True
)
```

**Paramètres:**
- `meteo_date_col: str = 'date'` - Colonne de date météo
- `rte_date_col: str = 'date'` - Colonne de date RTE
- `save_intermediate: bool = True` - Sauvegarder fichiers intermédiaires

**Retour:**
- `pd.DataFrame` - Dataset final clean

**Fichiers sauvegardés:**
- `01_meteo_raw.csv` - Météo brute fusionnée
- `02_rte_raw.csv` - RTE brute fusionnée
- `03_merged_raw.csv` - Fusion avant nettoyage
- `04_data_final.csv` - Final clean

**Logging:**
- Chaque étape est loggée en INFO
- Warnings si problèmes rencontrés
- Errors si impossible de continuer

---

## 6. Configuration

### PipelineConfig (dataclass)

```python
from scripts.config import PipelineConfig

config = PipelineConfig(
    meteo=MeteoConfig(),
    rte=RTEConfig(),
    fusion=FusionConfig(),
    quality=QualityConfig(),
    output_dir=Path("output"),
    log_level='INFO',
    save_intermediate=True,
    output_format='both'
)
```

### ConfigPresets

```python
from scripts.config import ConfigPresets

# Production
prod = ConfigPresets.production()  # log_level='WARNING'

# Development
dev = ConfigPresets.development()  # log_level='DEBUG'

# Testing
test = ConfigPresets.testing()     # output_dir='test_output'
```

---

## Importations

```python
# Classes principales
from scripts.data_pipeline import (
    MeteoDataPipeline,
    RTEDataPipeline,
    DataFusionPipeline,
    DataQualityPipeline,
    EnergyDataPipeline
)

# Configuration
from scripts.config import (
    PipelineConfig,
    ConfigPresets,
    MeteoConfig,
    RTEConfig,
    FusionConfig,
    QualityConfig
)

# Utilitaires
from scripts.utils import (
    get_project_paths,
    create_data_summary,
    save_data,
    load_data
)
```

---

## Examples de code complet

### Pipeline basique
```python
from pathlib import Path
from scripts.data_pipeline import EnergyDataPipeline

pipeline = EnergyDataPipeline(
    Path("data/Data_Climat"),
    Path("data/Data_eCO2"),
    Path("output")
)
df = pipeline.run()
df.to_csv("output/final.csv", index=False)
```

### Avec configuration personnalisée
```python
from scripts.config import PipelineConfig
from scripts.data_pipeline import EnergyDataPipeline

config = PipelineConfig()
config.quality.iqr_multiplier = 2.0
pipeline = EnergyDataPipeline(config.meteo.data_dir, config.rte.data_dir)
df = pipeline.run()
```

### Étape par étape
```python
from scripts.data_pipeline import *

meteo = MeteoDataPipeline(Path("data/Data_Climat")).load_and_clean_meteo()
rte = RTEDataPipeline(Path("data/Data_eCO2")).load_and_clean_rte()
merged = DataFusionPipeline.merge_datasets(meteo, rte)
final = DataQualityPipeline.handle_missing_values(merged)
```

---

## Type Hints

Toutes les fonctions utilisent les type hints :

```python
def load_and_clean_meteo(self) -> pd.DataFrame:
    """..."""

def merge_datasets(df_meteo: pd.DataFrame, 
                  df_rte: pd.DataFrame,
                  how: str = 'inner') -> pd.DataFrame:
    """..."""

def detect_and_report_outliers(
    df: pd.DataFrame,
    numeric_only: bool = True
) -> Dict[str, List[int]]:
    """..."""
```

---

## Notes de performance

- **Météo**: ~100 fichiers CSV = ~10s
- **RTE**: ~5 fichiers Excel = ~5s
- **Fusion**: ~100k rows = <1s
- **Nettoyage**: ~100k rows = ~2s
- **Total**: ~20s pour ~100k lignes

---

## Gestion des erreurs

```python
try:
    pipeline = EnergyDataPipeline(...)
    df = pipeline.run()
except FileNotFoundError as e:
    print(f"Répertoire manquant: {e}")
except ValueError as e:
    print(f"Données invalides: {e}")
except Exception as e:
    print(f"Erreur critique: {e}")
```

---

## Logging

```python
import logging

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Le pipeline loggue automatiquement toutes les étapes
# DEBUG: messages de débogage détaillés
# INFO: progression générale
# WARNING: problèmes non-bloquants
# ERROR: problèmes graves
```
