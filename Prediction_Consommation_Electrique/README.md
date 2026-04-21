# ⚡ Prédiction de la Consommation Électrique — Pipeline ML End-to-End

<div align="center">

![EDF](https://img.shields.io/badge/Contexte-EDF%20%7C%20Électricité%20de%20France-003189?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMyAyLjA1djIuMDJjMy45NS41NCA3IDMuOTkgNyA4LjQzIDAgMy40My0xLjkgNi41NC01IDguMjhsLTEuNS0xLjVjMi4yLTEuMzIgMy41LTMuNzMgMy41LTYuMjggMC0zLjY2LTIuNjgtNi43LTYtNy4xNXoiLz48L3N2Zz4=)
![XGBoost](https://img.shields.io/badge/Modèle-XGBoost-FF6600?style=for-the-badge&logo=python&logoColor=white)
![R² Score](https://img.shields.io/badge/R²%20Score-0.976-00C851?style=for-the-badge)
![MAPE](https://img.shields.io/badge/MAPE-2.02%25-00C851?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

**Pipeline ML complet pour la prédiction horaire de la consommation électrique française**  
*Météo-France + RTE eCO2mix · 14 Départements · Janvier 2025 – Janvier 2026*

</div>

---

## 🎯 Le Défi de l'Équilibre Énergétique

La consommation électrique française est un défi opérationnel permanent pour les gestionnaires de réseau. Elle fluctue de **25 000 à 45 000+ MW** selon l'heure, la météo et le calendrier — un écart de presque 100% entre les creux nocturnes et les pics hivernaux.

> *"Chaque degré Celsius de moins = une hausse significative de la demande nationale. Chaque heure mal prédite = un déséquilibre réseau coûteux."*

Ce projet répond à trois défis concrets :

| Défi | Description |
|------|-------------|
| ⚡ **Demande Variable** | La conso varie de 25 000 à 45 000+ MW selon l'heure, la météo et le calendrier |
| 🌡️ **Température Critique** | Corrélation de **-0.985** entre température et consommation |
| 📡 **Signal TEMPO RTE** | 3 types de jours (BLEU/BLANC/ROUGE) encodant le niveau de stress du réseau électrique |

**L'enjeu opérationnel** : des prévisions fiables permettent un meilleur équilibrage du réseau, un meilleur scheduling des ENR, et une gestion optimale des pics de demande.

---

## 🏆 Résultats en un coup d'œil

<div align="center">

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **R² Score** | `0.976` | 97.6% de la variance expliquée |
| **MAE** | `703 MW` | Erreur absolue moyenne |
| **RMSE** | `901 MW` | Erreur quadratique moyenne |
| **MAPE** | `2.02%` | Erreur relative moyenne |
| **Dataset** | `720 points` | Janv. 2025 – Janv. 2026 |

</div>

---

## 🔬 Feature Importance — Top 10 Prédicteurs

L'analyse XGBoost révèle une hiérarchie claire des drivers de consommation :

```
Heure du jour        ████████████████████████████████████  53.4%  ← #1 prédicteur
Température          ██████████████████████               30.3%  ← Corrélation -0.985
Lag 24 heures        ████████                             13.0%  ← Hier prédit aujourd'hui
Autres features      ██                                    3.3%  ← Humidité, ENR, calendrier
```

**Insights clés :**
- 🕐 **53.4% — Heure du jour** : Les pics matin/soir sont parfaitement capturés par le modèle
- 🌡️ **30.3% — Température** : Corrélation de -0.985, le froid = forte hausse de conso
- 🔁 **13.0% — Lag 24h** : La consommation d'hier prédit efficacement celle d'aujourd'hui
- 📊 **Top 3 = 97% de l'importance cumulée** — modèle lisible et explicable

---

## 🏗️ Architecture du Pipeline ML

Le projet est structuré en **5 étapes séquentielles** :

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  01          │    │  02               │    │  03                │    │  04              │    │  05               │
│  INGESTION   │───▶│  FUSION &         │───▶│  FEATURE           │───▶│  MODÉLISATION    │───▶│  EXPORT &         │
│              │    │  NETTOYAGE        │    │  ENGINEERING       │    │  XGBOOST         │    │  VISUALISATION    │
│ Météo-France │    │ 245 280 lignes    │    │ 43 features        │    │ Split temporel   │    │ CSV · Parquet     │
│ RTE eCO2mix  │    │ horaires          │    │ construites        │    │ strict           │    │ Power BI          │
└─────────────┘    └──────────────────┘    └───────────────────┘    └─────────────────┘    └──────────────────┘
```

**Stats du pipeline :**
- 📁 14 fichiers CSV Météo-France
- 📅 720 jours × 43 features
- ✂️ Split : Train **50%** · Val **21%** · Test **29%**
- ⚙️ XGBoost : `max_depth=6`, `lr=0.1`

### Fichiers du projet

```
Prediction_Consommation_Electrique/
├── main.py                          # Point d'entrée unique
├── predict.py                       # Entraînement + prédiction depuis dataset nettoyé
├── run_demo.py                      # Exécution sur sous-ensemble de données
├── requirements.txt
├── scripts/
│   ├── data_pipeline.py             # Ingestion, nettoyage, fusion Météo + RTE
│   ├── feature_engineering.py       # Construction des 43 variables explicatives
│   └── modeling.py                  # XGBoost, prédictions, importance des features
├── data/
│   ├── Data_Climat/                 # 14 fichiers CSV horaires Météo-France
│   └── Data_eCO2/                   # Données RTE (conso, production, CO2)
├── output/                          # Artefacts générés par le pipeline
├── notebooks/                       # Analyses exploratoires
└── logs/                            # Logs d'exécution
```

---

## ⚙️ Feature Engineering — Les 43 Variables

Les features construites couvrent 5 catégories :

| Catégorie | Features | Exemples |
|-----------|----------|---------|
| 🕐 **Temporelles** | Heure, jour, mois, saison | `hour`, `day_of_week`, `month` |
| 📅 **Calendaires** | Week-end, jours fériés, TEMPO | `is_weekend`, `tempo_type` |
| 🔁 **Lags** | Décalages temporels 1h/2h/24h | `lag_1`, `lag_2`, `lag_24` |
| 📊 **Rolling Mean** | Moyennes mobiles 6h/24h | `rolling_mean_6`, `rolling_mean_24` |
| 🔗 **Interactions** | Croisements de variables | `temp_x_weekend`, `temp_x_humidite` |

---

## 🚀 Lancer le projet

### Installation

```bash
git clone https://github.com/<votre-username>/Prediction_Consommation_Electrique.git
cd Prediction_Consommation_Electrique
pip install -r requirements.txt
```

### Exécution

```bash
# Pipeline complet (ingestion → features → modèle → export)
python main.py --mode full

# Préparation du dataset nettoyé uniquement
python main.py --mode prepare

# Entraînement + prédiction depuis dataset déjà nettoyé
python main.py --mode train_predict

# Démo rapide sur sous-ensemble
python run_demo.py
```

---

## 📦 Artefacts produits

| Fichier | Description |
|---------|-------------|
| `output/dataset_final_clean.csv` | Dataset fusionné et nettoyé (Météo + RTE) |
| `output/predictions.csv` | Date · Réel · Prédit · Erreurs (MAE, MAPE) |
| `output/feature_importance.csv` | Classement des 43 variables par importance XGBoost |

**Fichiers intermédiaires (audit / debug) :**
| Fichier | Étape |
|---------|-------|
| `output/01_meteo_raw.csv` | Après ingestion Météo-France |
| `output/02_rte_raw.csv` | Après ingestion RTE eCO2mix |
| `output/03_merged_raw.csv` | Après fusion Météo + RTE |
| `output/04_data_final.csv` | Après nettoyage complet |
| `output/features_engineered.csv` | Après feature engineering |

---

## 🧰 Stack Technique

```python
# Données
pandas · numpy · pyarrow

# Modélisation
xgboost · scikit-learn

# Visualisation
matplotlib · seaborn · Power BI

# Sources de données
# • Météo-France (données horaires, 14 départements)
# • RTE eCO2mix (consommation, production, signal TEMPO)
```

---

## 📈 Performances détaillées

Le modèle prédit la consommation horaire avec une **erreur relative moyenne de 2.02%** sur la période de test (26–30 janvier 2026), sans aucune fuite de données grâce au split temporel strict.

```
Test set : 26 – 30 janvier 2026
Split : Temporel strict (pas de shuffle)
Fuite de données : Aucune
```

**Pourquoi XGBoost ?**
- Robustesse aux valeurs manquantes
- Gestion native des features temporelles
- Interprétabilité via l'importance des features
- Performances supérieures aux baselines linéaires sur ce type de données

---

## 📁 Sources de données

| Source | Type | Couverture |
|--------|------|-----------|
| **Météo-France** | Données horaires climatiques | 14 départements français |
| **RTE eCO2mix** | Consommation, production, CO2, TEMPO | National · Jan 2025 – Jan 2026 |

---

<div align="center">

*Machine Learning · Météo-France + RTE eCO2mix · XGBoost Gradient Boosting*  
*Avril 2026*

</div>
