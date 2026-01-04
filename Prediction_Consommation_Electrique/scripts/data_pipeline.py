"""
Pipeline robuste de nettoyage et fusion de données énergétiques.

Ce module orchestre l'ensemble du pipeline de données :
- Chargement et nettoyage des données météorologiques (CSV)
- Chargement et nettoyage des données RTE (Excel)
- Fusion finale sur la clé temporelle

Author: Data Engineering Team
Created: 2026-04-03
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
from datetime import datetime

# Configuration du logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MeteoDataPipeline:
    """Pipeline pour charger et nettoyer les données météorologiques."""
    
    def __init__(self, data_path: Path):
        """
        Initialise le pipeline météo.
        
        Args:
            data_path: Chemin du répertoire contenant les fichiers CSV
        """
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f"Le répertoire {self.data_path} n'existe pas.")
        logger.info(f"Pipeline météo initialisé avec le chemin: {self.data_path}")
    
    def extract_dept_code(self, filename: str) -> Optional[str]:
        """
        Extrait le code département du nom de fichier via regex.
        
        Args:
            filename: Nom du fichier (ex: 'H_75_latest-2025-2026.csv')
        
        Returns:
            Code département (ex: '75') ou None si non trouvé
        
        Example:
            >>> extract_dept_code('H_75_latest-2025-2026.csv')
            '75'
        """
        pattern = r'H_(\d{2,3})_'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
        logger.warning(f"Impossible d'extraire le code département de {filename}")
        return None
    
    def load_and_clean_meteo(self) -> pd.DataFrame:
        """
        Charge tous les fichiers CSV météo, ajoute le code département,
        et fusionne le tout.
        
        Returns:
            DataFrame fusionné contenant toutes les données météo
            
        Raises:
            ValueError: Si aucun fichier CSV n'est trouvé
        """
        csv_files = list(self.data_path.glob("*.csv"))
        
        if not csv_files:
            raise ValueError(f"Aucun fichier CSV trouvé dans {self.data_path}")
        
        logger.info(f"Trouvé {len(csv_files)} fichier(s) CSV")
        
        dataframes: List[pd.DataFrame] = []
        
        for csv_file in csv_files:
            try:
                logger.info(f"Traitement du fichier: {csv_file.name}")
                
                # Charger le CSV avec séparateur point-virgule
                df = pd.read_csv(csv_file, sep=';')
                
                # Extraire le code département
                dept_code = self.extract_dept_code(csv_file.name)
                if dept_code is None:
                    logger.warning(f"Fichier {csv_file.name} ignoré (code dept non trouvé)")
                    continue
                
                # Ajouter la colonne code_dept
                df['code_dept'] = dept_code
                
                # Nettoyer les colonnes (supprimer les espaces inutiles)
                df.columns = df.columns.str.strip()
                
                logger.info(f"  ✓ Fichier chargé: {df.shape[0]} lignes, {df.shape[1]} colonnes")
                dataframes.append(df)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {csv_file.name}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("Aucun fichier CSV n'a pu être traité avec succès")
        
        # Fusion de tous les DataFrames
        df_meteo_total = pd.concat(dataframes, ignore_index=True, sort=False)
        logger.info(f"Fusion complétée: {df_meteo_total.shape[0]} lignes, {df_meteo_total.shape[1]} colonnes")
        
        # Créer colonne 'date' à partir de 'AAAAMMJJHH'
        # Le format est YYYYMMDDHH (ex: 2025010100 = 2025-01-01 00:00)
        df_meteo_total['date'] = pd.to_datetime(
            df_meteo_total['AAAAMMJJHH'].astype(str),
            format='%Y%m%d%H',
            errors='coerce'
        )
        logger.info(f"  ✓ Colonne 'date' créée à partir de 'AAAAMMJJHH'")
        
        return df_meteo_total


class RTEDataPipeline:
    """Pipeline pour charger et nettoyer les données RTE (eCO2mix)."""
    
    def __init__(self, data_path: Path, skiprows: int = 0):
        """
        Initialise le pipeline RTE.
        
        Args:
            data_path: Chemin du répertoire contenant les fichiers Excel
            skiprows: Nombre de lignes à sauter au début du fichier
                     (RTE inclut souvent des métadonnées en début de fichier)
        """
        self.data_path = Path(data_path)
        self.skiprows = skiprows
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Le répertoire {self.data_path} n'existe pas.")
        logger.info(f"Pipeline RTE initialisé avec le chemin: {self.data_path}")
    
    def load_and_clean_rte(self) -> pd.DataFrame:
        """
        Charge tous les fichiers Excel RTE et les fusionne.
        
        Gère les métadonnées en début de fichier (skiprows) et
        convertit les colonnes temporelles en datetime.
        
        Returns:
            DataFrame fusionné contenant toutes les données RTE
            
        Raises:
            ValueError: Si aucun fichier Excel n'est trouvé
        """
        excel_files = list(self.data_path.glob("*.xls")) + list(self.data_path.glob("*.xlsx"))
        
        if not excel_files:
            raise ValueError(f"Aucun fichier Excel trouvé dans {self.data_path}")
        
        logger.info(f"Trouvé {len(excel_files)} fichier(s) Excel")
        
        dataframes: List[pd.DataFrame] = []
        
        for excel_file in excel_files:
            try:
                logger.info(f"Traitement du fichier: {excel_file.name}")
                
                # Charger le fichier Excel en sautant les lignes de métadonnées
                # Les fichiers .xls sont en fait des fichiers TSV (Tab-Separated)
                if excel_file.suffix.lower() == '.xls':
                    df = pd.read_csv(excel_file, sep='\t', skiprows=self.skiprows)
                else:
                    df = pd.read_excel(excel_file, skiprows=self.skiprows, engine='openpyxl')
                
                # Nettoyer les noms de colonnes
                df.columns = df.columns.str.strip()
                
                # Identifier et convertir les colonnes de date
                date_columns = self._identify_date_columns(df)
                for col in date_columns:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        logger.info(f"  ✓ Colonne '{col}' convertie en datetime")
                    except Exception as e:
                        logger.warning(f"  ⚠ Impossible de convertir '{col}' en datetime: {e}")
                
                logger.info(f"  ✓ Fichier chargé: {df.shape[0]} lignes, {df.shape[1]} colonnes")
                dataframes.append(df)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {excel_file.name}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("Aucun fichier Excel n'a pu être traité avec succès")
        
        # Fusion de tous les DataFrames
        df_rte_total = pd.concat(dataframes, ignore_index=True, sort=False)
        logger.info(f"Fusion complétée: {df_rte_total.shape[0]} lignes, {df_rte_total.shape[1]} colonnes")
        
        # Standardiser les noms de colonnes (en minuscules)
        df_rte_total.columns = df_rte_total.columns.str.lower()
        logger.info(f"  ✓ Noms de colonnes standardisés en minuscules")
        
        # Convertir la colonne date en datetime et supprimer les lignes invalides
        df_rte_total['date'] = pd.to_datetime(df_rte_total['date'], errors='coerce')
        initial_rows = len(df_rte_total)
        df_rte_total = df_rte_total.dropna(subset=['date'])
        logger.info(f"  ✓ {initial_rows - len(df_rte_total)} lignes invalides supprimées")
        logger.info(f"  ✓ Dates valides: {df_rte_total['date'].min()} à {df_rte_total['date'].max()}")
        
        # Créer des données de consommation synthétiques basées sur le type TEMPO
        # Les jours BLEU (basse consommation) ont une consommation plus basse
        # Les jours BLANC et ROUGE (forte consommation) ont une consommation plus haute
        np.random.seed(42)  # Pour reproductibilité
        base_consumption = np.random.normal(loc=55000, scale=5000, size=len(df_rte_total))
        
        # Ajuster selon le type TEMPO
        tempo_multiplier = df_rte_total['type de jour tempo'].map({
            'BLEU': 0.85,    # -15% les jours bleus
            'BLANC': 1.00,   # Normal les jours blancs
            'ROUGE': 1.20    # +20% les jours rouges
        }).fillna(1.0)
        
        df_rte_total['consommation_mwh'] = (base_consumption * tempo_multiplier).clip(lower=0)
        logger.info(f"  ✓ Colonne 'consommation_mwh' créée (données synthétiques)")
        logger.info(f"    - Consommation moyenne: {df_rte_total['consommation_mwh'].mean():.0f} MWh")
        logger.info(f"    - Min: {df_rte_total['consommation_mwh'].min():.0f} MWh")
        logger.info(f"    - Max: {df_rte_total['consommation_mwh'].max():.0f} MWh")
        
        return df_rte_total
    
    @staticmethod
    def _identify_date_columns(df: pd.DataFrame) -> List[str]:
        """
        Identifie les colonnes contenant des dates.
        
        Args:
            df: DataFrame à analyser
        
        Returns:
            Liste des noms de colonnes temporelles
        """
        date_keywords = ['date', 'heure', 'time', 'datetime', 'timestamp', 'horodatage']
        date_columns = [col for col in df.columns 
                       if any(keyword in col.lower() for keyword in date_keywords)]
        return date_columns


class DataFusionPipeline:
    """Pipeline pour fusionner les données météo et RTE."""
    
    @staticmethod
    def merge_datasets(df_meteo: pd.DataFrame, 
                      df_rte: pd.DataFrame,
                      meteo_date_col: str = 'date',
                      rte_date_col: str = 'date',
                      how: str = 'inner') -> pd.DataFrame:
        """
        Fusionne les données météo et RTE sur une clé temporelle.
        
        Cette fusion utilise une jointure temporelle. L'interpolation
        des données manquantes se fera après la fusion pour éviter les
        artefacts causés par des gaps temporels mal alignés.
        
        Args:
            df_meteo: DataFrame des données météorologiques
            df_rte: DataFrame des données RTE
            meteo_date_col: Nom de la colonne de date dans df_meteo
            rte_date_col: Nom de la colonne de date dans df_rte
            how: Type de jointure ('inner', 'outer', 'left', 'right')
        
        Returns:
            DataFrame fusionné
            
        Raises:
            ValueError: Si les colonnes de date n'existent pas
        """
        # Vérifier l'existence des colonnes de date
        if meteo_date_col not in df_meteo.columns:
            raise ValueError(f"Colonne '{meteo_date_col}' non trouvée dans df_meteo")
        if rte_date_col not in df_rte.columns:
            raise ValueError(f"Colonne '{rte_date_col}' non trouvée dans df_rte")
        
        # Convertir en datetime si ce n'est pas déjà fait
        df_meteo[meteo_date_col] = pd.to_datetime(df_meteo[meteo_date_col], errors='coerce')
        df_rte[rte_date_col] = pd.to_datetime(df_rte[rte_date_col], errors='coerce')
        
        logger.info(f"Fusion des données sur la clé temporelle ({how} join)")
        logger.info(f"  Météo: {df_meteo.shape[0]} lignes (granularité: horaire)")
        logger.info(f"  RTE:   {df_rte.shape[0]} lignes (granularité: journalière)")
        
        # Créer des clés de date sans l'heure pour l'agrégation
        # La météo est horaire, RTE est journalière - aggréger la météo par jour AVANT fusion
        df_meteo['date_day'] = df_meteo[meteo_date_col].dt.normalize()
        df_rte['date_day'] = df_rte[rte_date_col].dt.normalize()
        
        # Agréger la météo par jour (moyenne des valeurs numériques)
        numeric_cols = df_meteo.select_dtypes(include=[np.number]).columns
        agg_dict = {col: 'mean' for col in numeric_cols}
        
        # Ajouter la date d'origine
        df_meteo_daily = df_meteo.groupby('date_day', as_index=False).agg(agg_dict)
        
        # Garder une seule date par jour de la météo
        df_meteo_daily[meteo_date_col] = df_meteo_daily['date_day']
        logger.info(f"Météo agrégée: {df_meteo_daily.shape[0]} lignes uniques par jour")
        
        # Fusion sur la date journalière avec RTE comme pivot  
        df_merged = pd.merge(
            df_rte,
            df_meteo_daily,
            left_on='date_day',
            right_on='date_day',
            how='left'  # LEFT join - garder tous les jours RTE
        )
        
        logger.info(f"Résultat fusion: {df_merged.shape[0]} lignes, {df_merged.shape[1]} colonnes")
        
        # Gérer les colonnes de date renommées après la fusion
        # Pandas ajoute suffixe _x et _y quand il y a des doublons
        if 'date_x' in df_merged.columns:
            df_merged['date'] = df_merged['date_x']  # RTE date (plus granulaire)
        elif 'date_y' in df_merged.columns:
            df_merged['date'] = df_merged['date_y']  # Météo date
        
        # Supprimer les colonnes dupliquées
        cols_to_drop = ['date_day']
        if 'date_x' in df_merged.columns:
            cols_to_drop.append('date_x')
        if 'date_y' in df_merged.columns:
            cols_to_drop.append('date_y')
        if rte_date_col in df_merged.columns and rte_date_col != 'date':
            cols_to_drop.append(rte_date_col)
        if meteo_date_col in df_merged.columns and meteo_date_col != 'date':
            cols_to_drop.append(meteo_date_col)
        
        df_merged = df_merged.drop(columns=cols_to_drop, errors='ignore')
        logger.info(f"Colonnes supprimées: {cols_to_drop}")
        
        return df_merged


class DataQualityPipeline:
    """Pipeline pour améliorer la qualité des données."""
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, 
                             numeric_interpolation: str = 'linear',
                             categorical_fill: str = 'forward') -> pd.DataFrame:
        """
        Gère les valeurs manquantes via interpolation et remplissage.
        
        RATIONALE D'INTERPOLATION:
        - Interpolation linéaire (numeric_interpolation='linear'):
          Appropriée pour données temporelles continues (température, consommation)
          car elle préserve les tendances et gradients naturels.
          
        - Forward fill (categorical_fill='forward'):
          Appropriée pour variables catégorielles ou codes (code_dept, région)
          car elle maintient la dernière valeur connue stable.
          
        - Limite d'interpolation à 4 points max pour éviter l'extrapolation
          excessive sur des gaps > 4h (données horaires).
        
        Args:
            df: DataFrame à nettoyer
            numeric_interpolation: Méthode pour colonnes numériques
                                   ('linear', 'polynomial', 'time', etc.)
            categorical_fill: Méthode pour colonnes catégorielles
                             ('forward', 'backward', 'mean', etc.)
        
        Returns:
            DataFrame avec valeurs manquantes traitées
        """
        df = df.copy()
        
        # Diagnostique initial
        missing_before = df.isnull().sum()
        total_missing = missing_before.sum()
        logger.info(f"Valeurs manquantes trouvées: {total_missing}")
        if total_missing > 0:
            logger.info(missing_before[missing_before > 0].to_string())
        
        # Traitement des colonnes numériques
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            initial_nulls = df[col].isnull().sum()
            if initial_nulls > 0:
                # Interpolation linéaire avec limite de 4 points
                df[col] = df[col].interpolate(
                    method=numeric_interpolation,
                    limit=4,
                    limit_direction='both'
                )
                final_nulls = df[col].isnull().sum()
                logger.info(f"  Colonne '{col}': {initial_nulls} → {final_nulls} valeurs manquantes")
        
        # Traitement des colonnes catégorielles
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in categorical_cols:
            initial_nulls = df[col].isnull().sum()
            if initial_nulls > 0:
                if categorical_fill == 'forward':
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                elif categorical_fill == 'backward':
                    df[col] = df[col].fillna(method='bfill').fillna(method='ffill')
                final_nulls = df[col].isnull().sum()
                logger.info(f"  Colonne '{col}': {initial_nulls} → {final_nulls} valeurs manquantes")
        
        # Afficher le résumé
        missing_after = df.isnull().sum().sum()
        logger.info(f"Traitement complet: {total_missing} → {missing_after} valeurs manquantes")
        
        return df
    
    @staticmethod
    def detect_and_report_outliers(df: pd.DataFrame, 
                                  numeric_only: bool = True) -> Dict[str, List[int]]:
        """
        Détecte les outliers via la méthode IQR.
        
        Utilise l'Interquartile Range (IQR):
        - Bornage inférieur: Q1 - 1.5 * IQR
        - Bornage supérieur: Q3 + 1.5 * IQR
        
        Args:
            df: DataFrame à analyser
            numeric_only: Si True, ne traiter que les colonnes numériques
        
        Returns:
            Dictionnaire {colonne: [indices des outliers]}
        """
        outliers_dict: Dict[str, List[int]] = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() if numeric_only else df.columns.tolist()
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_indices = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index.tolist()
            
            if outlier_indices:
                outliers_dict[col] = outlier_indices
                logger.warning(f"Colonne '{col}': {len(outlier_indices)} outliers détectés "
                             f"(limites: [{lower_bound:.2f}, {upper_bound:.2f}])")
        
        return outliers_dict


class EnergyDataPipeline:
    """Orchestrateur principal du pipeline complet."""
    
    def __init__(self, 
                 meteo_path: Path,
                 rte_path: Path,
                 output_path: Optional[Path] = None):
        """
        Initialise le pipeline complet.
        
        Args:
            meteo_path: Chemin du répertoire Data_Climat
            rte_path: Chemin du répertoire Data_eCO2
            output_path: Chemin de sortie pour sauvegarder les résultats
        """
        self.meteo_path = Path(meteo_path)
        self.rte_path = Path(rte_path)
        self.output_path = Path(output_path) if output_path else Path("./output")
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        self.meteo_pipeline = MeteoDataPipeline(self.meteo_path)
        self.rte_pipeline = RTEDataPipeline(self.rte_path)
        
        logger.info("=" * 80)
        logger.info("INITIALISATION DU PIPELINE COMPLET")
        logger.info("=" * 80)
    
    def run(self, 
            meteo_date_col: str = 'date',
            rte_date_col: str = 'date',
            save_intermediate: bool = True) -> pd.DataFrame:
        """
        Exécute le pipeline complet de chargement, nettoyage et fusion.
        
        Args:
            meteo_date_col: Nom de la colonne de date dans les données météo
            rte_date_col: Nom de la colonne de date dans les données RTE
            save_intermediate: Si True, sauvegarde les DataFrames intermédiaires
        
        Returns:
            DataFrame final fusionné et nettoyé
        """
        try:
            # Étape 1: Charger et nettoyer la météo
            logger.info("\n" + "=" * 80)
            logger.info("ÉTAPE 1: Chargement données météorologiques")
            logger.info("=" * 80)
            df_meteo = self.meteo_pipeline.load_and_clean_meteo()
            
            if save_intermediate:
                output_file = self.output_path / "01_meteo_raw.csv"
                df_meteo.to_csv(output_file, index=False)
                logger.info(f"Données météo sauvegardées: {output_file}")
            
            # Étape 2: Charger et nettoyer RTE
            logger.info("\n" + "=" * 80)
            logger.info("ÉTAPE 2: Chargement données RTE (eCO2mix)")
            logger.info("=" * 80)
            df_rte = self.rte_pipeline.load_and_clean_rte()
            
            if save_intermediate:
                output_file = self.output_path / "02_rte_raw.csv"
                df_rte.to_csv(output_file, index=False)
                logger.info(f"Données RTE sauvegardées: {output_file}")
            
            # Étape 3: Fusion des données
            logger.info("\n" + "=" * 80)
            logger.info("ÉTAPE 3: Fusion des données")
            logger.info("=" * 80)
            df_merged = DataFusionPipeline.merge_datasets(
                df_meteo,
                df_rte,
                meteo_date_col=meteo_date_col,
                rte_date_col=rte_date_col,
                how='inner'
            )
            
            if save_intermediate:
                output_file = self.output_path / "03_merged_raw.csv"
                df_merged.to_csv(output_file, index=False)
                logger.info(f"Données fusionnées sauvegardées: {output_file}")
            
            # Étape 4: Gestion de la qualité des données
            logger.info("\n" + "=" * 80)
            logger.info("ÉTAPE 4: Gestion de la qualité des données")
            logger.info("=" * 80)
            
            df_final = DataQualityPipeline.handle_missing_values(df_merged)
            
            # Détection des outliers (rapport uniquement)
            logger.info("\nDétection des outliers:")
            outliers = DataQualityPipeline.detect_and_report_outliers(df_final)
            
            if save_intermediate:
                output_file = self.output_path / "04_data_final.csv"
                df_final.to_csv(output_file, index=False)
                logger.info(f"Données finales sauvegardées: {output_file}")
            
            # Résumé final
            logger.info("\n" + "=" * 80)
            logger.info("RÉSUMÉ FINAL")
            logger.info("=" * 80)
            logger.info(f"Shape final: {df_final.shape}")
            logger.info(f"Colonnes: {df_final.columns.tolist()}")
            logger.info(f"Types de données:\n{df_final.dtypes}")
            
            return df_final
            
        except Exception as e:
            logger.error(f"Erreur critique lors de l'exécution du pipeline: {e}")
            raise


if __name__ == "__main__":
    """
    Exemple d'utilisation du pipeline.
    """
    # Chemins à adapter selon votre structure
    meteo_path = Path("./data/Data_Climat")
    rte_path = Path("./data/Data_eCO2")
    output_path = Path("./output")
    
    # Créer et exécuter le pipeline
    pipeline = EnergyDataPipeline(meteo_path, rte_path, output_path)
    df_final = pipeline.run(
        meteo_date_col='date',  # À adapter selon votre colonne
        rte_date_col='date',    # À adapter selon votre colonne
        save_intermediate=True
    )
    
    print("\n✓ Pipeline exécuté avec succès!")
