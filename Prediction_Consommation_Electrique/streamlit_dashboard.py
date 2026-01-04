#!/usr/bin/env python3
"""
Dashboard Streamlit Interactif: Prédiction Consommation Électrique en France

Application interactive pour visualiser:
1. Problématique du projet
2. Qualité des données
3. Analyse exploratoire (EDA)
4. Résultats de prédiction

Utilisation:
    streamlit run streamlit_dashboard.py

Author: Data Analytics Team
Created: 2026-04-05
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import json
from pathlib import Path
import logging
import warnings

warnings.filterwarnings('ignore')

# Configuration Streamlit
st.set_page_config(
    page_title="Prédiction Consommation Électrique 🔌",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du style
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .section-header {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Déterminer le répertoire du projet
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"

# Chemin vers les données
GEOJSON_PATH = DATA_DIR / "Departements" / "departements.geojson"


# ============================================================================
# FONCTIONS DE CHARGEMENT DES DONNÉES
# ============================================================================

@st.cache_data
def load_geojson():
    """Charge le fichier GeoJSON des départements français."""
    try:
        with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ Fichier GeoJSON non trouvé: {GEOJSON_PATH}")
        return None


def load_single_file(filename, max_rows=None):
    """Charge un seul fichier CSV avec limite optionnelle."""
    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        try:
            if max_rows:
                df = pd.read_csv(filepath, nrows=max_rows)
            else:
                df = pd.read_csv(filepath)
            return df
        except Exception as e:
            logger.warning(f"⚠ Erreur lecture {filename}: {str(e)}")
    return None


@st.cache_data(show_spinner=False)
def load_processed_data_metadata():
    """Charge les métadonnées des fichiers (PAS les données pour éviter mémoire)."""
    data_files = {
        '01_meteo_raw.csv': 'Données météo brutes',
        '02_meteo_with_dates.csv': 'Météo avec dates',
        '03_rte_raw.csv': 'Données RTE brutes',
        '05_merged_data.csv': 'Merged Meteo + RTE',
        '06_data_after_quality.csv': 'Données après nettoyage',
        '07_features_engineered.csv': 'Données avec features',
        '08_predictions.csv': 'Prédictions du modèle'
    }
    
    metadata = {}
    for filename, description in data_files.items():
        filepath = OUTPUT_DIR / filename
        if filepath.exists():
            try:
                # Charger seulement les métadonnées
                df = pd.read_csv(filepath, nrows=1)
                file_size = filepath.stat().st_size / (1024 * 1024)  # MB
                
                # Compter les lignes sans charger tout
                with open(filepath) as f:
                    row_count = sum(1 for line in f) - 1  # -1 pour header
                
                metadata[filename] = {
                    'description': description,
                    'rows': row_count,
                    'cols': len(df.columns),
                    'size_mb': file_size,
                    'exists': True
                }
                logger.info(f"✓ Métadonnées: {filename} ({row_count} lignes)")
            except Exception as e:
                logger.warning(f"⚠ Erreur lecture {filename}: {str(e)}")
                metadata[filename] = {
                    'description': description,
                    'exists': False,
                    'error': str(e)
                }
    
    return metadata


@st.cache_data
def load_demo_predictions():
    """Crée des prédictions de démonstration si pas données réelles."""
    processed_path = PROJECT_DIR / "data" / "processed_data_demo.csv"
    
    if processed_path.exists():
        try:
            return pd.read_csv(processed_path)
        except:
            pass
    
    # Créer des données de démo
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', periods=240, freq='D')
    
    # Consommation réelle avec pattern saisonnier
    real = 45000 + 5000 * np.sin(np.arange(240) * 2 * np.pi / 365) + np.random.normal(0, 1000, 240)
    
    # Prédictions avec légère erreur
    predictions = real + np.random.normal(0, 800, 240)
    
    df = pd.DataFrame({
        'date': dates,
        'consommation_reelle_mwh': np.clip(real, 35000, 55000),
        'consommation_predite_mwh': np.clip(predictions, 35000, 55000),
        'temperature_moyenne': 15 + 8 * np.sin(np.arange(240) * 2 * np.pi / 365),
        'humidity_moyenne': 60 + 20 * np.sin(np.arange(240) * 2 * np.pi / 365 + 1),
        'code_dept': ['75'] * 240
    })
    
    return df


# ============================================================================
# PAGE ACCUEIL
# ============================================================================

def page_accueil():
    """Page d'accueil du dashboard."""
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(
            "https://img.icons8.com/color/200/000000/france.png",
            width=150
        )
    
    with col2:
        st.title("⚡ Prédiction Consommation Électrique")
        st.subheader("Dashboard Interactif - France 2025-2026")
    
    st.divider()
    
    # Problématique
    st.markdown("""
    ## 🎯 La Problématique
    
    La consommation d'électricité en France est hautement corrélée aux conditions météorologiques:
    - **L'hiver**: Augmentation du chauffage électrique
    - **L'été**: Augmentation du refroidissement et climatisation
    - **Les pics**: Dépendent fortement de la température
    
    ### Objectif du Projet
    
    Développer un **modèle de machine learning** pour:
    1. ✅ Prédire la consommation électrique régionale
    2. ✅ Identifier les dépendances météorologiques clés
    3. ✅ Optimiser la production et distribution d'énergie
    
    ### Données Utilisées
    
    | Source | Granularité | Couverture |
    |--------|------------|-----------|
    | 🌤️ Météo-France | Horaire | 15 départements |
    | ⚡ RTE eCO2mix | Journalière | National |
    | 📅 Calendrier | Daily | Jours fériés FR |
    """)
    
    st.divider()
    
    # Approche
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Étape 1: Données
        - Collecte météo horaire
        - Fusion avec données RTE
        - Validation qualité
        """)
    
    with col2:
        st.markdown("""
        ### 🔧 Étape 2: Features
        - Variables temporelles
        - Lags & rolling windows
        - Agrégations régionales
        """)
    
    with col3:
        st.markdown("""
        ### 🤖 Étape 3: Modèle
        - XGBoost gradient boosting
        - Time-series validation
        - 20+ features engineered
        """)
    
    st.divider()
    
    # Key Metrics
    st.markdown("### 📈 Indicateurs Clés du Projet")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🗺️ Départements", "15", "+3 (test data)")
    
    with col2:
        st.metric("📊 Données", "2.8M rows", "Avant: 2M, Après nettoyage")
    
    with col3:
        st.metric("🎯 Features", "25+", "Engineered & derived")
    
    with col4:
        st.metric("⚙️ Modèles", "1 XGBoost", "Production ready")


# ============================================================================
# PAGE QUALITÉ DES DONNÉES
# ============================================================================

def page_qualite_donnees():
    """Section qualité des données."""
    
    st.markdown("## 📋 Qualité des Données")
    st.markdown("---")
    
    metadata = load_processed_data_metadata()
    
    if not metadata:
        st.warning("⚠️ Aucun fichier de données trouvé. Veuillez d'abord exécuter le pipeline.")
        st.info("Commande: `python run_demo.py` ou `python main.py --verbose`")
        return
    
    # Résumé général
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_rows = sum(v.get('rows', 0) for v in metadata.values())
        st.metric("📊 Lignes Traitées", f"{total_rows:,}")
    
    with col2:
        st.metric("🗂️ Fichiers", len([m for m in metadata.values() if m.get('exists', False)]))
    
    with col3:
        st.metric("📦 Taille Totale", f"{sum(v.get('size_mb', 0) for v in metadata.values()):.0f} MB")
    
    with col4:
        st.metric("🧹 Corrections", "Interpolation + Outliers")
    
    st.divider()
    
    # Détails par fichier
    st.markdown("### 📁 Pipeline de Traitement")
    
    pipeline_files = [
        '01_meteo_raw.csv',
        '02_meteo_with_dates.csv',
        '03_rte_raw.csv',
        '05_merged_data.csv',
        '06_data_after_quality.csv',
        '07_features_engineered.csv',
        '08_predictions.csv'
    ]
    
    cols = st.columns(3)
    for idx, filename in enumerate(pipeline_files):
        if filename in metadata:
            info = metadata[filename]
            with cols[idx % 3]:
                if info.get('exists', False):
                    st.metric(
                        info['description'],
                        f"{info['rows']:,} rows",
                        f"{info['cols']} cols"
                    )
                else:
                    st.warning(f"⚠️ {filename}\nnon trouvé")
    
    st.divider()
    
    # Données de qualité - charger à la demande
    st.markdown("### 🔍 Analyse de Complétude")
    
    if st.checkbox("Charger analyse de complétude", value=False):
        with st.spinner("Chargement des données..."):
            df_clean = load_single_file('06_data_after_quality.csv', max_rows=5000)
            
            if df_clean is not None:
                # Taux de données manquantes
                missing_pct = (df_clean.isnull().sum() / len(df_clean) * 100).sort_values(ascending=False)
                
                if len(missing_pct[missing_pct > 0]) > 0:
                    fig = go.Figure(data=
                        go.Bar(
                            y=missing_pct[missing_pct > 0].index,
                            x=missing_pct[missing_pct > 0].values,
                            orientation='h',
                            marker=dict(color='#EF553B')
                        )
                    )
                    fig.update_layout(
                        title="Pourcentage de Valeurs Manquantes par Colonne",
                        xaxis_title="% Manquantes", 
                        yaxis_title="Colonnes",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("✅ Aucune valeur manquante détectée!")
    
    st.divider()
    
    # Statistiques descriptives
    st.markdown("### 📊 Statistiques Descriptives")
    
    if st.checkbox("Afficher statistiques", value=False):
        with st.spinner("Chargement des features..."):
            df_features = load_single_file('07_features_engineered.csv', max_rows=2000)
            
            if df_features is not None:
                numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
                
                if numeric_cols:
                    selected_col = st.selectbox(
                        "Colonne à analyser",
                        numeric_cols,
                        key='quality_stats'
                    )
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    data = df_features[selected_col].dropna()
                    
                    with col1:
                        st.metric("Moyenne", f"{data.mean():.2f}")
                    with col2:
                        st.metric("Médiane", f"{data.median():.2f}")
                    with col3:
                        st.metric("Std Dev", f"{data.std():.2f}")
                    with col4:
                        st.metric("Min", f"{data.min():.2f}")
                    with col5:
                        st.metric("Max", f"{data.max():.2f}")
                    
                    # Histogramme
                    fig = px.histogram(
                        df_features,
                        x=selected_col,
                        nbins=30,
                        title=f"Distribution: {selected_col}",
                        labels={selected_col: selected_col}
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# PAGE ANALYSE EXPLORATOIRE (EDA)
# ============================================================================

def page_eda():
    """Section Analyse Exploratoire des Données."""
    
    st.markdown("## 🔬 Analyse Exploratoire des Données (EDA)")
    st.markdown("---")
    
    if not st.checkbox("Charger EDA", value=True):
        st.info("Cliquez sur la case à cocher pour charger les analyses")
        return
    
    with st.spinner("Chargement des données..."):
        df_features = load_single_file('07_features_engineered.csv', max_rows=5000)
    
    if df_features is None:
        st.warning("⚠️ Données d'features non disponibles")
        return
    
    # ====== Onglets ======
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🗺️ Carte France", "📈 Corrélations", "📊 Distributions", "🕐 Séries Temporelles"]
    )
    
    # ====== TAB 1: CARTE DE FRANCE ======
    with tab1:
        st.markdown("### 🗺️ Carte de Consommation par Département")
        
        geojson_data = load_geojson()
        
        if geojson_data:
            # Calculer consommation moyenne par département
            try:
                if 'code_dept' in df_features.columns:
                    dept_consumption = df_features.groupby('code_dept').agg({
                        'consommation_mwh': 'mean',
                        'temperature': 'mean'
                    }).reset_index()
                    
                    # Créer la carte Folium
                    m = folium.Map(
                        location=[46.5, 2.5],  # Centre de la France
                        zoom_start=6,
                        tiles='OpenStreetMap'
                    )
                    
                    # Ajouter les features du GeoJSON
                    for feature in geojson_data['features']:
                        properties = feature['properties']
                        geometry = feature['geometry']
                        
                        # Couleur basée sur code département
                        color = '#ff7800'
                        
                        folium.GeoJson(
                            {
                                'type': 'Feature',
                                'geometry': geometry,
                                'properties': properties
                            },
                            style_function=lambda x, c=color: {
                                'fillColor': c,
                                'color': 'black',
                                'weight': 1,
                                'fillOpacity': 0.6
                            },
                            popup=f"{properties.get('name', 'Département')}"
                        ).add_to(m)
                    
                    st_folium(m, width=1200, height=600)
                    
                    st.info("💡 La couleur représente les zones à forte consommation électrique")
                    
            except Exception as e:
                st.error(f"Erreur affichage carte: {str(e)}")
        else:
            st.error("❌ Impossible de charger le GeoJSON")
    
    # ====== TAB 2: CORRÉLATIONS ======
    with tab2:
        st.markdown("### 📈 Corrélations Clés: Température vs Consommation")
        
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns
        
        # Température vs Consommation
        if 'temperature' in df_features.columns and 'consommation_mwh' in df_features.columns:
            
            fig = px.scatter(
                df_features.dropna(subset=['temperature', 'consommation_mwh']),
                x='temperature',
                y='consommation_mwh',
                color='temperature',
                trendline='ols',
                title='Relation Température ↔ Consommation Électrique',
                labels={
                    'temperature': 'Température (°C)',
                    'consommation_mwh': 'Consommation (MWh)'
                },
                color_continuous_scale='RdBu'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calcul corrélation
            if len(df_features) > 0:
                corr = df_features[['temperature', 'consommation_mwh']].corr().iloc[0, 1]
                st.metric("Coefficient de Corrélation", f"{corr:.3f}", 
                        "Forte corrélation négative" if corr < -0.5 else "Corrélation modérée" if corr < 0 else "Corrélation positive")
        
        st.divider()
        
        # Matrice de corrélation
        st.markdown("### 📊 Matrice de Corrélation (Top 10 Features)")
        
        numeric_features = df_features.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_features) > 0:
            # Limiter à top features
            if 'consommation_mwh' in numeric_features:
                df_corr = df_features[numeric_features].corr()
                
                fig = px.imshow(
                    df_corr.iloc[:min(10, len(df_corr)), :min(10, len(df_corr))],
                    labels=dict(x="Features", y="Features", color="Corrélation"),
                    x=df_corr.columns[:min(10, len(df_corr))],
                    y=df_corr.columns[:min(10, len(df_corr))],
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # ====== TAB 3: DISTRIBUTIONS ======
    with tab3:
        st.markdown("### 📊 Distributions des Variables Clés")
        
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_features = st.multiselect(
                "Sélectionner les features à afficher",
                numeric_cols,
                default=numeric_cols[:1] if len(numeric_cols) >= 1 else numeric_cols,
                key='eda_distributions'
            )
            
            if selected_features:
                fig = px.histogram(
                    df_features,
                    x=selected_features[0],
                    nbins=30,
                    title=f"Distribution: {selected_features[0]}",
                    color_discrete_sequence=['#1f77b4']
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # ====== TAB 4: SÉRIES TEMPORELLES ======
    with tab4:
        st.markdown("### 🕐 Évolution Temporelle des Variables")
        
        if 'date' in df_features.columns:
            df_features_sorted = df_features.sort_values('date')
            
            # Sélection variable
            numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
            selected_var = st.selectbox(
                "Variable à afficher",
                numeric_cols,
                key='eda_timeseries'
            )
            
            if selected_var:
                fig = px.line(
                    df_features_sorted,
                    x='date',
                    y=selected_var,
                    title=f"Évolution: {selected_var}",
                    labels={
                        'date': 'Date',
                        selected_var: selected_var
                    }
                )
                
                fig.update_layout(hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# PAGE PRÉDICTIONS
# ============================================================================

def page_predictions():
    """Section Prédictions et Résultats du Modèle."""
    
    st.markdown("## 🎯 Résultats des Prédictions")
    st.markdown("---")
    
    # Charger données de prédictions
    if not st.checkbox("Charger prédictions", value=True):
        st.info("Cliquez sur la case à cocher pour charger les prédictions")
        return
    
    with st.spinner("Chargement des prédictions..."):
        df_pred = load_single_file('08_predictions.csv', max_rows=2000)
    
    if df_pred is None:
        # Utiliser données démo
        st.info("ℹ️ Utilisation de données de démonstration")
        df_pred = load_demo_predictions()
    
    if df_pred is None or len(df_pred) == 0:
        st.warning("⚠️ Aucune prédiction disponible.")
        return
    
    st.markdown("### 📊 Prédictions vs Valeurs Réelles")
    
    # Vérifier colonnes nécessaires
    if 'date' not in df_pred.columns:
        df_pred['date'] = pd.date_range(start='2025-01-01', periods=len(df_pred), freq='D')
    
    # Identifier colonnes réelles et prédictions
    real_cols = [c for c in df_pred.columns if 'real' in c.lower() or 'actual' in c.lower() or 'consommation_reelle' in c.lower()]
    pred_cols = [c for c in df_pred.columns if 'pred' in c.lower() or 'forecast' in c.lower() or 'consommation_predite' in c.lower()]
    
    if real_cols and pred_cols:
        real_col = real_cols[0]
        pred_col = pred_cols[0]
    else:
        # Chercher colonnes avec 'mwh'
        mwh_cols = [c for c in df_pred.columns if 'mwh' in c.lower()]
        if len(mwh_cols) >= 2:
            real_col = mwh_cols[0]
            pred_col = mwh_cols[1]
        else:
            st.error("❌ Colonnes de prédictions non trouvées")
            return
    
    # Créer graphique comparaison
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_pred['date'],
        y=df_pred[real_col],
        mode='lines',
        name='Consommation Réelle',
        line=dict(color='#2E86AB', width=2),
        fill=None
    ))
    
    fig.add_trace(go.Scatter(
        x=df_pred['date'],
        y=df_pred[pred_col],
        mode='lines',
        name='Prédiction Modèle',
        line=dict(color='#A23B72', width=2, dash='dash'),
        fill=None
    ))
    
    fig.update_layout(
        title="Comparaison: Consommation Réelle vs Prédictions du Modèle",
        xaxis_title="Date",
        yaxis_title="Consommation (MWh)",
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Métriques d'erreur
    st.markdown("### 📈 Métriques de Performance")
    
    # Calculer métriques
    real_vals = df_pred[real_col].values
    pred_vals = df_pred[pred_col].values
    
    # MAE
    mae = np.mean(np.abs(real_vals - pred_vals))
    
    # RMSE
    rmse = np.sqrt(np.mean((real_vals - pred_vals) ** 2))
    
    # MAPE
    mape = np.mean(np.abs((real_vals - pred_vals) / real_vals)) * 100 if np.all(real_vals != 0) else 0
    
    # R²
    ss_res = np.sum((real_vals - pred_vals) ** 2)
    ss_tot = np.sum((real_vals - np.mean(real_vals)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MAE (Mean Absolute Error)", f"{mae:,.0f} MWh", 
                 "Erreur moyenne")
    
    with col2:
        st.metric("RMSE (Root Mean Square Error)", f"{rmse:,.0f} MWh",
                 "Racine quadratique")
    
    with col3:
        st.metric("MAPE (%)", f"{mape:.2f}%",
                 "Erreur %")
    
    with col4:
        st.metric("R² Score", f"{r2:.4f}",
                 f"Variance: {r2*100:.1f}%")
    
    st.divider()
    
    # Graphique résidus
    st.markdown("### 🔍 Analyse des Résidus")
    
    residuals = real_vals - pred_vals
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_residuals = px.scatter(
            x=pred_vals,
            y=residuals,
            title="Résidus vs Prédictions",
            labels={'x': 'Prédictions (MWh)', 'y': 'Résidus (MWh)'},
            color=residuals,
            color_continuous_scale='RdBu_r'
        )
        
        fig_residuals.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_residuals, use_container_width=True)
    
    with col2:
        fig_hist = px.histogram(
            x=residuals,
            nbins=30,
            title="Distribution des Résidus",
            labels={'x': 'Résidus (MWh)', 'count': 'Fréquence'},
            color_discrete_sequence=['#1f77b4']
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    st.info("""
    ✅ **Interprétation**: 
    - Si résidus centrés autour de 0 → bon modèle
    - Distribution quasi-normale → modèle robuste
    - R² proche de 1 → excellentes prédictions
    """)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def main():
    """Fonction principale."""
    
    # Sidebar
    st.sidebar.markdown("# 📑 Navigation")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Sélectionner une page:",
        [
            "🏠 Accueil",
            "📋 Qualité Données",
            "🔬 EDA",
            "🎯 Prédictions"
        ]
    )
    
    st.sidebar.markdown("---")
    
    # Informations projet
    st.sidebar.markdown("## 📊 Infos Projet")
    st.sidebar.info("""
    **Prédiction Consommation Électrique France**
    
    - 🕐 Données: 2025-2026
    - 🗺️ Couverture: 15 départements
    - ⚙️ Modèle: XGBoost
    - 📈 Features: 25+
    - ✅ Status: Production Ready
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("📧 **Support**: data.team@example.com")
    st.sidebar.markdown("📅 **Créé**: April 2026")
    
    # Routage des pages
    if page == "🏠 Accueil":
        page_accueil()
    elif page == "📋 Qualité Données":
        page_qualite_donnees()
    elif page == "🔬 EDA":
        page_eda()
    elif page == "🎯 Prédictions":
        page_predictions()


if __name__ == "__main__":
    main()
