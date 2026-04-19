# Prediction de consommation electrique

Ce projet entraine un modele de regression pour predire la consommation electrique a partir des donnees meteo et des donnees RTE.

## Architecture du projet

### Fichiers principaux
- `main.py`: point d'entree unique pour executer le pipeline.
- `scripts/data_pipeline.py`: ingestion, nettoyage, fusion des donnees meteo + RTE.
- `scripts/feature_engineering.py`: creation des variables explicatives.
- `scripts/modeling.py`: entrainement XGBoost, predictions et importance des features.
- `scripts/prediction_pipeline.py`: orchestration complete.
- `predict.py`: entrainement + prediction a partir d'un dataset nettoye.
- `run_demo.py`: execution sur un sous-ensemble de donnees.

### Dossiers
- `data/Data_Climat/`: fichiers meteo horaires.
- `data/Data_eCO2/`: fichiers RTE (consommation, production, CO2).
- `output/`: sorties generees par le pipeline.

## Etapes de traitement

1. Chargement des fichiers meteo et RTE.
2. Conversion des dates, tri chronologique, suppression des doublons.
3. Fusion meteo/RTE sur la colonne `date`.
4. Interpolation simple des valeurs numeriques manquantes.
5. Generation de features:
   - calendaires (`hour`, `day_of_week`, `month`, `day_of_year`, `is_weekend`)
   - retard (`consommation_mwh_lag_1`, `lag_2`, `lag_24`)
   - rolling mean (`window 6`, `window 24`)
   - interactions (`temp_x_weekend`, `temp_x_humidite`)
6. Split temporel strict:
   - train: 70%
   - validation: 15%
   - test: 15%
7. Entrainement du modele XGBoost.
8. Generation des predictions et calcul des erreurs.
9. Export des fichiers finaux.

## Commandes d'execution

Installation:

```bash
pip install -r requirements.txt
```

Pipeline complet:

```bash
python main.py --mode full
```

Preparation seule du dataset nettoye:

```bash
python main.py --mode prepare
```

Entrainement + prediction a partir de `output/dataset_final_clean.csv`:

```bash
python main.py --mode train_predict
```

## Artefacts produits

Les livrables cibles sont:
- `output/dataset_final_clean.csv`
- `output/predictions.csv`
- `output/feature_importance.csv`

Fichiers intermediaires (debug / audit):
- `output/01_meteo_raw.csv`
- `output/02_rte_raw.csv`
- `output/03_merged_raw.csv`
- `output/04_data_final.csv`
- `output/features_engineered.csv`

## Lecture rapide des sorties

- `dataset_final_clean.csv`: dataset fusionne et nettoye.
- `predictions.csv`: date, consommation reelle, consommation predite, erreurs.
- `feature_importance.csv`: classement des variables les plus importantes pour le modele.
