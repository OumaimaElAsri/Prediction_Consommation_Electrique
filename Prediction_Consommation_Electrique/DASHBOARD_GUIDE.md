# 🎨 Dashboard Streamlit - Guide Complet

## 🚀 Démarrage Rapide

### Étape 1: Installation (1 minute)
```bash
# Activer l'environnement virtuel
.venv\Scripts\activate

# Installer/mettre à jour les dépendances
pip install -r requirements.txt --upgrade
```

### Étape 2: Générer les Données (2 minutes)
```bash
# Créer les données de test
python generate_test_data.py

# OU si vous avez les vraies données
python main.py --verbose
```

### Étape 3: Lancer le Dashboard (1 minute)
```bash
# Depuis le répertoire du projet
streamlit run streamlit_dashboard.py

# Cela ouvrira automatiquement: http://localhost:8501
```

---

## 📊 Vue d'Ensemble du Dashboard

### 🏠 **Page Accueil**
- **Objectif du projet**: Prédire la consommation électrique française
- **Approche**: Données → Features → Modèle
- **Indicateurs clés**: 15 départements, 2.8M rows, 25+ features

### 📋 **Page Qualité des Données** 
Affiche les indicateurs essentiels de traitement des données:

```
✅ Lignes Traitées:  Nombre total de lignes dans le pipeline
✅ Fichiers Traitées: Différentes étapes du pipeline
✅ Complétude: % de données sans valeurs manquantes
✅ Corrections Appliquées: Interpolation + Détection d'outliers
```

**Visualisations:**
- 📊 Taux de complétude par colonne
- 📈 Statistiques descriptives (moyenne, médiane, std dev, min, max)
- 📁 Pipeline de traitement complet

### 🔬 **Page EDA (Analyse Exploratoire)**

#### 1️⃣ **Onglet "Carte France"**
- 🗺️ Affiche la carte interactive de la France
- Colorée par **intensité de consommation électrique**
- Utilise le fichier `departements.geojson`
- **Interaction**: Zoom, pan, survol pour détails

#### 2️⃣ **Onglet "Corrélations"**
- 📈 **Graphique scatter**: Température vs Consommation
- Avec ligne de tendance (régression linéaire)
- Coefficient de corrélation calculé
- 🔥 **Matrice de corrélation** (top 10 features)

#### 3️⃣ **Onglet "Distributions"**
- 📊 Histogrammes des variables clés
- Sélection multiple de features
- Analyse des patterns de distribution

#### 4️⃣ **Onglet "Séries Temporelles"**
- 🕐 Évolution des variables dans le temps
- Sélection dynamique des variables
- Hover interactif

### 🎯 **Page Prédictions**

#### Graphique Principal: **Consommation Réelle vs Prédictions**
- Ligne bleue: **Valeurs réelles** (historique)
- Ligne pointillée rose: **Prédictions du modèle**
- Hover interactif pour voir valeurs exactes
- Zoom/pan pour inspection détaillée

#### Métriques de Performance:

| Métrique | Description | Interprétation |
|----------|-------------|-----------------|
| **MAE** | Mean Absolute Error | Erreur moyenne (en MWh) |
| **RMSE** | Root Mean Square Error | Pénalise les grandes erreurs |
| **MAPE** | Mean Absolute Percentage Error | Erreur en pourcentage |
| **R²** | Coefficient de Détermination | Variance expliquée (0-1) |

#### Analyse des Résidus:
- 📊 **Graphique résidus vs prédictions**: Détecte biais systématiques
- 📈 **Histogramme résidus**: Vérifie distribution normale
- ✅ **Interprétation**: Si résidus centrés autour de 0 → bon modèle

---

## 🎨 Fonctionnalités Interactives

### Multiselect & Dropdowns
```
- Sélectionner colonnes à analyser
- Choisir variables pour visualisation
- Filtrer par période temporelle
```

### Cartes Interactives
```
- Zoom avant/arrière (scroll wheel)
- Pan (drag & drop)
- Survol pour infos département
```

### Graphiques Plotly
```
- Zoom by dragging
- Double-click to reset
- Hover pour voir valeurs exactes
- Download as PNG (bouton caméra)
```

---

## 📊 Données Affichées

Le dashboard charge automatiquement:

```
output/
├── 01_meteo_raw.csv              ← Données brutes météo
├── 02_meteo_with_dates.csv       ← Météo nettoyée
├── 03_rte_raw.csv                ← Données RTE brutes
├── 05_merged_data.csv            ← Fusion meteo + RTE
├── 06_data_after_quality.csv     ← Après validation qualité
├── 07_features_engineered.csv    ← Avec ML features
└── 08_predictions.csv            ← Prédictions du modèle

data/
└── processed_data_demo.csv        ← Données démo si pas outputs
```

**Si pas fichiers détectés**: le dashboard génère automatiquement des données de **démonstration**.

---

## ⚙️ Configuration Streamlit

### Optimiser la Performance
```bash
# Lancer en mode dev (rechargement automatique)
streamlit run streamlit_dashboard.py --logger.level=info

# Ou avec moins de verbosité
streamlit run streamlit_dashboard.py --logger.level=error
```

### Configuration ~/.streamlit/config.toml
```toml
[server]
headless = true
maxUploadSize = 200

[client]
toolbarMode = "viewer"

[theme]
primaryColor = "#FF7F0E"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## 🔧 Troubleshooting

### ❌ **Erreur: Streamlit not found**
```bash
# Solution
pip install streamlit --upgrade

# Ou depuis requirements.txt
pip install -r requirements.txt
```

### ❌ **Erreur: GeoJSON not found**
```
Vérifier que le fichier existe:
data/Departements/departements.geojson
```

**Solution**: Créer un mapping manuel si GeoJSON manquent

### ❌ **Erreur: No predictions found**
```
Le dashboard génère automatiquement des données démo
Sinon, exécuter:
    python run_demo.py
    python main.py --verbose
```

### ❌ **Port 8501 déjà utilisé**
```bash
streamlit run streamlit_dashboard.py --server.port 8502
```

### ⚠️ **Lenteur/Latence**
- Vérifier taille fichiers CSV (> 100MB = lent)
- Utiliser caching Streamlit (@st.cache_data)
- Réduire dataset si trop volumineux

---

## 🎓 Architecture du Code

### Structure du Dashboard
```python
# Fonctions de chargement des données
load_geojson()                  # GeoJSON des départements
load_processed_data()            # Fichiers output/
load_demo_predictions()          # Données de démonstration

# Pages du dashboard
page_accueil()                   # 🏠 Vue d'accueil
page_qualite_donnees()          # 📋 Qualité & statistiques
page_eda()                       # 🔬 Analyse exploratoire
page_predictions()              # 🎯 Résultats & métriques

# Navigation
main()                          # Sidebar + routing
```

### Caching pour Performance
```python
@st.cache_data
def load_processed_data():
    # Exécuté une seule fois au lancement
    # Rechargé si fichier source change
    pass
```

---

## 📈 Cas d'Utilisation

### Pour les Stakeholders
- 🎤 Présentation executive du projet
- 📊 KPIs et métriques visibles
- 🗺️ Impact géographique visible

### Pour les Data Scientists
- 🔬 Explore corrélations et patterns
- 📈 Valider qualité des features
- 📉 Analyser performance du modèle

### Pour les Ingénieurs
- 🔧 Monitor pipeline data
- ✅ Vérifier complétude/qualité
- 📊 Diagnostiquer problèmes

---

## 🚀 Déploiement en Production

### Option 1: Cloud (Streamlit Cloud - GRATUIT)
```bash
# 1. Pousser code sur GitHub
git push origin main

# 2. Sur streamlit.io
# - Connecter GitHub
# - Sélectionner repository
# - Déployer automatiquement!

# URL: https://yourusername-appname.streamlit.app
```

### Option 2: Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_dashboard.py"]
```

```bash
docker build -t electricity-dashboard .
docker run -p 8501:8501 electricity-dashboard
```

### Option 3: AWS/GCP/Azure
- EC2/GCE instance + Streamlit
- Serverless (Lambda + CloudFront)
- K8s + Helm charts

---

## 📝 Personnalisation

### Changer les Couleurs
```python
# streamlit_dashboard.py
color_primary = "#1f77b4"      # Bleu
color_secondary = "#ff7f0e"    # Orange
color_danger = "#EF553B"       # Rouge
```

### Ajouter Nouvelles Pages
```python
if page == "📱 Ma Nouvelle Page":
    st.title("Nouvelle Analyse")
    # Votre code ici
```

### Ajouter Interactivité
```python
# Slider
threshold = st.slider("Seuil", min_value=0, max_value=100)

# Multiselect
departments = st.multiselect("Départements", options=[...])

# Download
st.download_button("Télécharger CSV", data=csv_data, ...)
```

---

## 📚 Ressources

- **Streamlit Docs**: https://docs.streamlit.io
- **Plotly**: https://plotly.com/python
- **Folium**: https://python-visualization.github.io/folium

---

## ✨ Fonctionnalités Sympas

✅ Cache des données pour performance rapide  
✅ Sidebar pour navigation facile  
✅ Cartes GeoJSON interactives  
✅ Graphiques Plotly responsifs  
✅ Génération auto de données démo  
✅ Dark mode support (via Streamlit settings)  
✅ Responsive design (mobile-friendly)  
✅ Métadonnes du projet dans sidebar  

---

**Dashboard Status**: ✅ **READY TO USE**  
**Last Updated**: April 5, 2026  
**Version**: 1.0
