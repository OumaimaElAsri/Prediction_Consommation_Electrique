# Data Projects | Projets Data

Collection of machine learning and data engineering projects.

Collection de projets d'apprentissage automatique et d'ingénierie des données.

---

## English Version

### Prediction_Consommation_Electrique

French electricity consumption prediction system using meteorological data and RTE energy mix information.

- **Status**: Production-ready
- **Tech Stack**: Python, XGBoost, Pandas, NumPy
- **Data**: 2.8M+ hourly observations across 15 French departments
- **Model Features**: 25+ engineered features with time-series validation
- **Output**: CSV and Parquet formats with predictions and error metrics

**Quick Start**:
```bash
cd Prediction_Consommation_Electrique
pip install -r requirements.txt
python main.py
```

**Details**: See `Prediction_Consommation_Electrique/README.md`

---

## Version Française

### Prediction_Consommation_Electrique

Système de prédiction de la consommation d'électricité en France utilisant les données météorologiques et le mix énergétique de RTE.

- **Statut**: Prêt pour la production
- **Stack Technique**: Python, XGBoost, Pandas, NumPy
- **Données**: 2.8M+ observations horaires sur 15 départements français
- **Features du Modèle**: 25+ features générées avec validation time-series
- **Sortie**: Formats CSV et Parquet avec prédictions et métriques d'erreur

**Démarrage Rapide**:
```bash
cd Prediction_Consommation_Electrique
pip install -r requirements.txt
python main.py
```

**Détails**: Voir `Prediction_Consommation_Electrique/README.md`

---

## Repository Structure | Structure du Dépôt

```
DataProjets/
├── README.md                                    (this file | ce fichier)
└── Prediction_Consommation_Electrique/
    ├── README.md                                (project docs | docs projet)
    ├── main.py
    ├── predict.py
    ├── requirements.txt
    ├── scripts/                                 (core modules | modules principaux)
    ├── data/                                    (meteorological and RTE data)
    ├── notebooks/                               (Jupyter analysis | analyse Jupyter)
    └── output/                                  (generated results | résultats générés)
```

---

## Environment Setup | Configuration de l'Environnement

Python 3.11+ required | Requis

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1           # Windows
source .venv/bin/activate             # Linux/Mac
pip install -r Prediction_Consommation_Electrique/requirements.txt
```

---

## Development | Développement

Each project is self-contained with its own requirements and documentation. Refer to individual project README files for specific instructions.

Chaque projet est autonome avec ses propres dépendances et documentation. Consultez les fichiers README des projets individuels pour les instructions spécifiques.

**GitHub Repository**: https://github.com/OumaimaElAsri/Prediction_Consommation_Electrique

