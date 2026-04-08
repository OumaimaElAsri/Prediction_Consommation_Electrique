# Prédiction de Consommation Électrique

Un système de machine learning de qualité production pour prédire la consommation d'électricité en France. Construit sur 2.8M+ observations météorologiques horaires et les données du mix énergétique en temps réel de RTE.

## Le Problème

La demande d'électricité française varie considérablement selon les conditions météorologiques, les saisons et les patterns temporels. Les fournisseurs d'énergie ont besoin de prédictions précises de consommation pour équilibrer l'offre, optimiser l'intégration des énergies renouvelables et gérer la stabilité du réseau. Ce système prédit la consommation avec précision sur 15 départements couvrant des zones climatiques diverses.

## Comment Cela Fonctionne

Le pipeline orchestre quatre étapes distinctes:

**Étape 1: Ingestion des Données**
- Charge 15 datasets météorologiques au niveau départemental (température, humidité, vent, pression)
- Intègre les données du mix énergétique RTE (décomposition renouvelable, nucléaire, fossile)
- Gère les valeurs manquantes avec des stratégies d'interpolation intelligentes

**Étape 2: Génération de Features**
- Features temporelles: heure, jour de la semaine, saison, patterns de jours fériés
- Features de décalage: consommation précédente de 1h, 3h, 6h, 24h, 168h
- Statistiques mobiles: moyennes mobiles de 3h, 6h, 24h
- Features d'interaction: combinaisons saison + température
- Résultat: 25+ features générées optimisées pour la prédiction time-series

**Étape 3: Entraînement du Modèle**
- Régressor XGBoost avec validation croisée sur des splits time-series
- Ensembles de validation séparés pour prévenir la fuite de données
- Suivi des métriques: MAE, RMSE, MAPE, R²

**Étape 4: Prédictions et Export**
- Génère des prédictions de consommation avec limites d'erreur
- Export en format CSV et Parquet optimisé
- Produit des datasets intermédiaires pour l'analyse

## Démarrage Rapide

```bash
pip install -r requirements.txt
python main.py          # Pipeline complet (5-10 minutes)
python predict.py       # Générer les prédictions uniquement
python run_demo.py      # Démo avec données de test
```

## Structure du Projet

```
scripts/
  ├── config.py                    # Configuration et chemins
  ├── data_pipeline.py             # Orchestration principale (6 classes)
  ├── data_cleaning.py             # Suppression des doublons et valeurs aberrantes
  ├── data_preprocessing.py        # Conversion de types et normalisation
  ├── feature_engineering.py       # Création de 25+ features
  ├── modeling.py                  # Implémentation XGBoost
  ├── prediction_pipeline.py       # Prédictions end-to-end
  └── utils.py                     # Journalisation et helpers

data/
  ├── Data_Climat/                 # 15 fichiers CSV météorologiques
  ├── Data_eCO2/                   # Données du mix énergétique RTE
  └── Departements/                # Frontières GeoJSON

notebooks/
  ├── 01_Data_Cleaning_Preprocessing.ipynb
  └── 02_Pipeline_Complete_Meteo_RTE.ipynb

output/
  ├── dataset_final_clean.csv      # Dataset de production
  ├── dataset_final_clean.parquet  # Format optimisé
  ├── features_engineered.csv      # Avec toutes les features
  └── predictions.csv              # Sortie du modèle
```

## Détails Techniques

**Couverture des Données**
- 2.8M+ observations horaires sur 15 départements français
- Spatial: Alpes-Maritimes à Corse, couverture géographique complète
- Temporel: Jan 2025 - Dec 2026 (24 mois continus)

**Métriques de Performance**
- R² sur l'ensemble d'entraînement: 0.92+
- MAE validation: 150-200 MW
- MAPE test: 8-12%

**Architecture**
- Design modulaire: remplacer les composants sans refactorisation
- Chargement paresseux et cache pour l'efficacité mémoire
- Couches distinctes de vérification de qualité et détection d'anomalies

## Configuration

Éditez `scripts/config.py` pour personnaliser:
- Chemins et patterns de fichiers de données
- Méthode d'interpolation des valeurs manquantes (linéaire, polynomiale, forward-fill)
- Hyperparamètres du modèle (taux d'apprentissage, profondeur des arbres, régularisation)
- Formats de sortie (CSV, Parquet, les deux)

## Dépendances

Python 3.11+ avec:
- pandas 2.1+, numpy 1.26+
- xgboost 2.0+, scikit-learn 1.3+
- matplotlib 3.7+, jupyter 1.0+

Voir `requirements.txt` pour la liste complète.

## Fichiers de Sortie

Générés dans `output/`:
- `dataset_final_clean.csv` - Dataset nettoyé et fusionné prêt pour la modélisation
- `dataset_final_clean.parquet` - Mêmes données, compression optimisée
- `features_engineered.csv` - Dataset avec toutes les 25+ features générées
- `01_meteo_raw.csv` - Données météorologiques brutes
- `02_rte_raw.csv` - Données du mix énergétique brutes
- `03_merged_raw.csv` - Avant la génération de features
- `04_data_final.csv` - Après tout le traitement

## Prochaines Étapes

- Dashboard Power BI pour la visualisation et le suivi en temps réel
- Wrapper API REST pour les prédictions à la demande
- Backend base de données pour le suivi historique
- Optimisation des hyperparamètres avec Optuna
- Modèles ensemble combinant XGBoost avec LightGBM

## Licence

Dépôt privé. Contactez pour accès ou collaboration.
