# 🚀 Quick Start Guide

## 5 Minutes pour démarrer le pipeline

### Étape 1: Installation (1 min)
```bash
cd Prediction_Consommation_Electrique/

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 2: Générer les données de test (1 min)
```bash
# Génère 3 départements × 30 jours de données
python generate_test_data.py
```

C'est tout! Les données sont créées dans:
```
data/
├── Data_Climat/
│   ├── H_75_latest-2025-2026.csv
│   ├── H_13_latest-2025-2026.csv
│   └── H_69_latest-2025-2026.csv
└── Data_eCO2/
    └── eCO2mix_RTE_tempo_2025-2026.csv
```

### Étape 3: Exécuter le pipeline (2 min)
```bash
# Lance le pipeline complet
python main.py

# Avec arguments personnalisés (optionnel)
python main.py --config development --verbose
```

### Étape 4: Vérifier les résultats (1 min)
```bash
# Voir les fichiers générés
ls -lh output/

# Afficher les premiers résultats
python -c "import pandas as pd; df = pd.read_csv('output/dataset_final_clean.csv'); print(df.head()); print(f'Shape: {df.shape}')"
```

---

## 📊 Résultats Attendus

Après exécution, vous devriez voir:

```
output/
├── 01_meteo_raw.csv           # Météo brute (2160 lignes)
├── 02_rte_raw.csv             # RTE brute (720 lignes)
├── 03_merged_raw.csv          # Fusion (720 lignes)
├── 04_data_final.csv          # Final clean ✅
└── dataset_final_clean.parquet # Format Parquet
```

Dataset final shape: `(720, 13)` (30 jours × 24h, 13 colonnes)

---

## 🔍 Explorer dans Python

```python
import pandas as pd
from scripts.data_pipeline import EnergyDataPipeline
from pathlib import Path

# Charger le résultat
df = pd.read_csv("output/dataset_final_clean.csv")

# Exploration basique
print(df.shape)           # (720, 13)
print(df.columns)         # Noms des colonnes
print(df.describe())      # Stats descriptives
print(df.isnull().sum())  # Valeurs manquantes

# Analyser les corrélations
print(df.corr())
```

---

## 📚 Notebook

Pour une analyse visuelle:

```bash
jupyter notebook notebooks/02_Pipeline_Complete_Meteo_RTE.ipynb
```

Dans le notebook:
1. Les imports sont déjà configurés
2. Les chemins sont automatiques
3. Les visualisations sont prêtes

---

## 🛠️ Troubleshooting

### Erreur: `No module named 'scripts'`
```bash
# Sûr d'être dans le bon répertoire
cd Prediction_Consommation_Electrique/
python main.py
```

### Erreur: `FileNotFoundError: data/Data_Climat`
```bash
# Générer les données
python generate_test_data.py
```

### Erreur: `ModuleNotFoundError: No module named 'pandas'`
```bash
# Réinstaller
pip install -r requirements.txt
```

### Erreur: `Permission denied`
```bash
# Sur Linux/Mac
chmod +x *.py
```

---

## 📈 Prochaines Étapes

1. **Remplacer les données de test** par vos vraies données dans `data/`
2. **Consulter la documentation** dans [README.md](README.md)
3. **Explorer les exemples** dans [examples.py](examples.py)
4. **Lire l'API** dans [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 🎯 Commandes Rapides

```bash
# Tout d'un coup
python generate_test_data.py && python main.py

# Configuration development
python main.py --config development --verbose

# Configuration production
python main.py --config production

# Sans fichiers intermédiaires
python main.py --no-intermediate

# Format de sortie personnalisé
python main.py --output-format parquet

# Tests unitaires
pytest scripts/test_data_pipeline.py -v

# Rapport de couverture
pytest scripts/test_data_pipeline.py --cov=scripts --cov-report=html
```

---

## 💡 Tips

- **Données de test**: ~2 secondes pour 3 depts × 30 jours
- **Pipeline complet**: ~10 secondes sur données test
- **Logs détaillés**: Vérifier `logs/pipeline_*.log`
- **Déboguer**: Ajouter `--verbose` au main.py
- **Paralléliser**: Voir `examples.py` pour patterns avancés

---

## ✨ C'est fait!

Vous avez maintenant un pipeline production-ready pour:
- ✅ Charger données météo CSV
- ✅ Charger données RTE Excel
- ✅ Fusionner sur clé temporelle
- ✅ Nettoyer les données
- ✅ Exporter CSV/Parquet

Prêt pour la modélisation ! 🎓

---

*Pour plus de détails, consultez [README.md](README.md) et [API_DOCUMENTATION.md](API_DOCUMENTATION.md)*
