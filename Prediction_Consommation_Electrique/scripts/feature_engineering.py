"""
Feature Engineering pour la prédiction de consommation électrique.

Module avancé pour :
- Agrégation de la météo à maille régionale
- Features calendaires spécifiques à la France
- Variables lag et rolling
- Normalisation et sélection de features

Author: Senior Data Scientist
Created: 2026-04-03
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging
import holidays

# Configuration du logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Mapping des départements vers régions climatiques françaises
# Basé sur les variations climatiques, géographie et zones de consommation
DEPT_TO_REGION = {
    # Île-de-France
    '75': 'Ile-de-France', '77': 'Ile-de-France', '78': 'Ile-de-France',
    '91': 'Ile-de-France', '92': 'Ile-de-France', '93': 'Ile-de-France',
    '94': 'Ile-de-France', '95': 'Ile-de-France',
    
    # Auvergne-Rhône-Alpes
    '01': 'Auvergne-Rhone-Alpes', '03': 'Auvergne-Rhone-Alpes',
    '07': 'Auvergne-Rhone-Alpes', '15': 'Auvergne-Rhone-Alpes',
    '42': 'Auvergne-Rhone-Alpes', '43': 'Auvergne-Rhone-Alpes',
    '63': 'Auvergne-Rhone-Alpes', '69': 'Auvergne-Rhone-Alpes',
    '73': 'Auvergne-Rhone-Alpes', '74': 'Auvergne-Rhone-Alpes',
    
    # Occitanie
    '09': 'Occitanie', '11': 'Occitanie', '12': 'Occitanie',
    '30': 'Occitanie', '31': 'Occitanie', '32': 'Occitanie',
    '34': 'Occitanie', '46': 'Occitanie', '48': 'Occitanie',
    '65': 'Occitanie', '66': 'Occitanie', '81': 'Occitanie',
    '82': 'Occitanie',
    
    # Nouvelle-Aquitaine
    '16': 'Nouvelle-Aquitaine', '17': 'Nouvelle-Aquitaine',
    '19': 'Nouvelle-Aquitaine', '23': 'Nouvelle-Aquitaine',
    '24': 'Nouvelle-Aquitaine', '33': 'Nouvelle-Aquitaine',
    '40': 'Nouvelle-Aquitaine', '47': 'Nouvelle-Aquitaine',
    '64': 'Nouvelle-Aquitaine', '79': 'Nouvelle-Aquitaine',
    '86': 'Nouvelle-Aquitaine', '87': 'Nouvelle-Aquitaine',
    
    # Provence-Alpes-Côte d'Azur
    '04': 'PACA', '05': 'PACA', '06': 'PACA',
    '13': 'PACA', '83': 'PACA', '84': 'PACA',
    
    # Bourgogne-Franche-Comté
    '21': 'Bourgogne-Franche-Comte', '25': 'Bourgogne-Franche-Comte',
    '39': 'Bourgogne-Franche-Comte', '58': 'Bourgogne-Franche-Comte',
    '70': 'Bourgogne-Franche-Comte', '71': 'Bourgogne-Franche-Comte',
    '89': 'Bourgogne-Franche-Comte', '90': 'Bourgogne-Franche-Comte',
    
    # Bretagne
    '22': 'Bretagne', '29': 'Bretagne', '35': 'Bretagne', '56': 'Bretagne',
    
    # Normandie
    '14': 'Normandie', '27': 'Normandie', '50': 'Normandie',
    '61': 'Normandie', '76': 'Normandie',
    
    # Pays de la Loire
    '44': 'Pays-de-la-Loire', '49': 'Pays-de-la-Loire',
    '53': 'Pays-de-la-Loire', '72': 'Pays-de-la-Loire', '85': 'Pays-de-la-Loire',
    
    # Centre-Val de Loire
    '18': 'Centre-Val-de-Loire', '28': 'Centre-Val-de-Loire',
    '36': 'Centre-Val-de-Loire', '37': 'Centre-Val-de-Loire',
    '41': 'Centre-Val-de-Loire', '45': 'Centre-Val-de-Loire',
    
    # Grand Est
    '08': 'Grand-Est', '10': 'Grand-Est', '51': 'Grand-Est',
    '52': 'Grand-Est', '54': 'Grand-Est', '55': 'Grand-Est',
    '57': 'Grand-Est', '67': 'Grand-Est', '68': 'Grand-Est', '88': 'Grand-Est',
    
    # Hauts-de-France
    '02': 'Hauts-de-France', '59': 'Hauts-de-France',
    '60': 'Hauts-de-France', '62': 'Hauts-de-France', '80': 'Hauts-de-France',
    
    # DROM-COM
    '974': 'La-Reunion', '971': 'Guadeloupe', '972': 'Martinique',
    '976': 'Mayotte', '973': 'Guyane',
}


class FeatureEngineer:
    """Classe pour le feature engineering avancé."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialise le feature engineer.
        
        Args:
            df: DataFrame fusionné (météo + RTE)
        """
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        logger.info(f"Feature Engineer initialisé avec {len(self.df)} lignes")
    
    def aggregate_meteo_to_regions(self) -> pd.DataFrame:
        """
        Agrège les données météorologiques par région climatique.
        
        RATIONALE D'AGRÉGATION:
        ========================
        Problem: Météo = maille départementale (15 depts)
                 RTE = maille nationale/régionale
        
        Solution: Agréger par région climatique
        Avantages:
        - Réduit le bruit (moyenne de plusieurs depts)
        - Représente les variations climatiques major
        - Correspond mieux à la maille de la consommation
        - Plus robuste aux données manquantes
        
        Méthode:
        1. Mapper code_dept → région climatique
        2. Grouper par date + région
        3. Moyenner les variables météo
        4. Moyenner la région (agrégation nationale)
        
        Returns:
            DataFrame agrégé
        """
        logger.info("Agrégation de la météo par région climatique...")
        
        # Vérifier que code_dept existe
        if 'code_dept' not in self.df.columns:
            logger.warning("Colonne 'code_dept' non trouvée, pas d'agrégation")
            return self.df
        
        # Mapper département → région
        self.df['region'] = self.df['code_dept'].map(DEPT_TO_REGION)
        
        # Identifier les colonnes météo (numériques sauf date, code_dept, region, conso)
        meteo_cols = [col for col in self.df.select_dtypes(include=[np.number]).columns
                     if col not in ['code_dept', 'consommation_mwh', 'production_eolienne_mwh', 
                                   'production_solaire_mwh', 'production_nucleaire_mwh',
                                   'production_hydro_mwh', 'co2_g_kwh']]
        
        if not meteo_cols:
            return self.df
        
        logger.info(f"Colonnes météo à agréger: {meteo_cols}")
        
        # Agrégation par date + région
        df_regional = self.df.groupby(['date', 'region'])[meteo_cols].mean().reset_index()
        
        # Agrégation nationale (moyenne sur toutes régions)
        df_national_meteo = df_regional.groupby('date')[meteo_cols].mean()
        
        # Récupérer les données RTE (une seule ligne par date)
        df_rte_only = self.df[['date', 'consommation_mwh']].drop_duplicates(subset=['date'])
        
        # Fusionner
        df_agg = df_rte_only.merge(df_national_meteo.reset_index(), on='date', how='left')
        
        logger.info(f"Agrégation complétée: {len(df_agg)} jours")
        return df_agg
    
    def add_calendar_features(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Ajoute des features calendaires spécifiques à la France.
        
        Features crées:
        - jour_semaine: 0-6 (lundi-dimanche)
        - est_weekend: 1 si samedi/dimanche
        - jour_ferie: 1 si jour férié français
        - mois: 1-12
        - jour_annee: 1-365
        - saison: 1-4 (hiver, printemps, été, automne)
        - trimestre: 1-4
        
        Args:
            df: DataFrame à enrichir (défaut: self.df)
        
        Returns:
            DataFrame avec features calendaires
        """
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()
        
        logger.info("Ajout des features calendaires...")
        
        # Jour de semaine (0=lundi, 6=dimanche)
        df['jour_semaine'] = df['date'].dt.dayofweek
        
        # Weekend
        df['est_weekend'] = (df['jour_semaine'] >= 5).astype(int)
        
        # Jours fériés français
        fr_holidays = holidays.France(years=range(2024, 2027))
        df['jour_ferie'] = df['date'].dt.date.map(lambda x: 1 if x in fr_holidays else 0)
        
        # Mois
        df['mois'] = df['date'].dt.month
        
        # Jour de l'année
        df['jour_annee'] = df['date'].dt.dayofyear
        
        # Saison (critère météorologique France)
        # Hiver: 12, 1, 2 | Printemps: 3, 4, 5 | Été: 6, 7, 8 | Automne: 9, 10, 11
        saison_map = {
            12: 1, 1: 1, 2: 1,      # Hiver
            3: 2, 4: 2, 5: 2,       # Printemps
            6: 3, 7: 3, 8: 3,       # Été
            9: 4, 10: 4, 11: 4      # Automne
        }
        df['saison'] = df['mois'].map(saison_map)
        
        # Trimestre
        df['trimestre'] = df['date'].dt.quarter
        
        # Heure de la journée (pour données horaires)
        if 'heure' in df.columns:
            df['heure'] = pd.to_datetime(df['heure']).dt.hour
        
        logger.info(f"Features calendaires ajoutées: {len(df)} lignes")
        return df
    
    def add_lag_features(self, 
                        df: Optional[pd.DataFrame] = None,
                        target_col: str = 'consommation_mwh',
                        lags: list = [1, 7, 24]) -> pd.DataFrame:
        """
        Ajoute des variables lag (décalées temporelles).
        
        Lag features:
        - J-1: consommation hier
        - J-7: consommation il y a 7 jours (pattern hebdomadaire)
        - J-24: consommation il y a 24 heures (si données horaires)
        
        Args:
            df: DataFrame à enrichir
            target_col: Colonne cible pour les lags
            lags: Liste des décalages (ex: [1, 7, 24])
        
        Returns:
            DataFrame avec features lag
        """
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()
        
        logger.info(f"Ajout des features lag pour {target_col}...")
        
        # Trier par date pour garantir l'ordre temporel
        df = df.sort_values('date').reset_index(drop=True)
        
        for lag in lags:
            col_name = f'{target_col}_lag_{lag}'
            df[col_name] = df[target_col].shift(lag)
            logger.info(f"  Lag {lag}: {col_name}")
        
        # Ajouter des rolling averages aussi (utile pour XGBoost)
        for window in [7, 30]:
            col_name = f'{target_col}_rolling_mean_{window}'
            df[col_name] = df[target_col].rolling(window=window, min_periods=1).mean()
            logger.info(f"  Rolling {window}d: {col_name}")
        
        return df
    
    def add_interaction_features(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Ajoute des features d'interaction pertinentes.
        
        Interactions créées:
        - temperature × jour_ferie (pics de chaleur jours fériés)
        - est_weekend × heure (patterns différents)
        - saison × temperature
        
        Args:
            df: DataFrame à enrichir
        
        Returns:
            DataFrame avec features interaction
        """
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()
        
        logger.info("Ajout des features interaction...")
        
        # Interactions basiques
        if 'temperature' in df.columns and 'jour_ferie' in df.columns:
            df['temp_x_ferie'] = df['temperature'] * df['jour_ferie']
        
        if 'est_weekend' in df.columns and 'heure' in df.columns:
            df['weekend_x_heure'] = df['est_weekend'] * df['heure']
        
        if 'saison' in df.columns and 'temperature' in df.columns:
            df['saison_x_temp'] = df['saison'] * df['temperature']
        
        logger.info("Features interaction ajoutées")
        return df
    
    def build_all_features(self) -> pd.DataFrame:
        """
        Construit tous les features d'un coup.
        
        Pipeline:
        1. Agrégation météo par région
        2. Features calendaires
        3. Variables lag
        4. Features interaction
        
        Returns:
            DataFrame complètement enrichi
        """
        logger.info("=" * 80)
        logger.info("CONSTRUCTION COMPLÈTE DES FEATURES")
        logger.info("=" * 80)
        
        # Étape 1
        df = self.aggregate_meteo_to_regions()
        
        # Étape 2
        df = self.add_calendar_features(df)
        
        # Étape 3
        df = self.add_lag_features(df)
        
        # Étape 4
        df = self.add_interaction_features(df)
        
        # Supprimer les lignes avec NaN causés par les lags (que les premières)
        # Ne pas supprimer les colonnes originales qui peuvent avoir des NaN légitimes
        initial_rows = len(df)
        
        # Supprimer seulement les NaN dans les colonnes de lag et rolling mean
        lag_cols = [col for col in df.columns if 'lag' in col or 'rolling' in col]
        if lag_cols:
            df = df.dropna(subset=lag_cols)
        
        removed = initial_rows - len(df)
        logger.info(f"Lignes supprimées (valeurs manquantes aux lags): {removed}")
        logger.info(f"Lignes conservées: {len(df)}")
        
        logger.info(f"\nDimension finale: {df.shape}")
        logger.info(f"Colonnes: {list(df.columns)}")
        
        return df


def create_feature_dataset(df_merged: pd.DataFrame, 
                          output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Fonction wrapper pour créer le dataset avec features complet.
    
    Args:
        df_merged: DataFrame fusionné (sortie du pipeline de cleaning)
        output_path: Chemin optionnel pour sauvegarde intermédiaire
    
    Returns:
        DataFrame avec toutes les features
    """
    engineer = FeatureEngineer(df_merged)
    df_features = engineer.build_all_features()
    
    if output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder
        csv_file = output_path / "features_engineered.csv"
        df_features.to_csv(csv_file, index=False)
        logger.info(f"Features sauvegardées: {csv_file}")
    
    return df_features


if __name__ == "__main__":
    """Exemple d'utilisation."""
    # Charger les données nettoyées
    from scripts.data_pipeline import EnergyDataPipeline
    
    pipeline = EnergyDataPipeline(
        Path("data/Data_Climat"),
        Path("data/Data_eCO2"),
        Path("output")
    )
    
    df_merged = pipeline.run(save_intermediate=False)
    
    # Feature Engineering
    df_features = create_feature_dataset(df_merged, Path("output"))
    
    print(df_features.head())
    print(df_features.describe())
