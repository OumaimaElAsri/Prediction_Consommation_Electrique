"""
Exemples d'utilisation avancée du pipeline énergétique.

Ce fichier montre différentes stratégies d'utilisation du pipeline
selon les cas d'usage et les besoins.

Author: Senior Data Engineer
Created: 2026-04-03
"""

from pathlib import Path
import pandas as pd
import logging

from scripts.data_pipeline import (
    EnergyDataPipeline,
    MeteoDataPipeline,
    RTEDataPipeline,
    DataFusionPipeline,
    DataQualityPipeline
)
from scripts.config import ConfigPresets, PipelineConfig


# Setup logging pour les exemples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# EXEMPLE 1: Pipeline complet basique
# ============================================================================
def example_basic_pipeline():
    """
    Exécuter le pipeline complet avec configuration par défaut.
    
    Cas d'usage: Fusion simple météo + RTE.
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 1: Pipeline Complet Basique")
    logger.info("=" * 80)
    
    pipeline = EnergyDataPipeline(
        meteo_path=Path("data/Data_Climat"),
        rte_path=Path("data/Data_eCO2"),
        output_path=Path("output")
    )
    
    df_final = pipeline.run(save_intermediate=True)
    
    print(f"\n✓ Dataset final: {df_final.shape}")
    return df_final


# ============================================================================
# EXEMPLE 2: Pipeline production avec configuration optimisée
# ============================================================================
def example_production_pipeline():
    """
    Pipeline pour l'environnement de production.
    
    Optimisations:
    - Pas de fichiers intermédiaires
    - Logging réduit (WARNING only)
    - Format Parquet (plus compact)
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 2: Pipeline Production")
    logger.info("=" * 80)
    
    # Charger la config production
    config = ConfigPresets.production()
    
    pipeline = EnergyDataPipeline(
        meteo_path=config.meteo.data_dir,
        rte_path=config.rte.data_dir,
        output_path=config.output_dir
    )
    
    df_final = pipeline.run(save_intermediate=False)
    
    # Sauvegarder en Parquet (meilleure compression)
    output_file = config.output_dir / "dataset_final.parquet"
    df_final.to_parquet(output_file, compression='snappy')
    print(f"\n✓ Dataset sauvegardé: {output_file}")
    
    return df_final


# ============================================================================
# EXEMPLE 3: Étapes individuelles avec contrôle fin
# ============================================================================
def example_step_by_step():
    """
    Exécuter le pipeline étape par étape.
    
    Cas d'usage: Besoin de contrôle granulaire entre les étapes.
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 3: Étapes Individuelles")
    logger.info("=" * 80)
    
    # --- ÉTAPE 1: Charger les données météo ---
    logger.info("\n[ÉTAPE 1] Chargement données météo...")
    meteo_pipeline = MeteoDataPipeline(Path("data/Data_Climat"))
    df_meteo = meteo_pipeline.load_and_clean_meteo()
    print(f"  Shape: {df_meteo.shape}")
    print(f"  Colonnes: {df_meteo.columns.tolist()}")
    
    # --- ÉTAPE 2: Charger les données RTE ---
    logger.info("\n[ÉTAPE 2] Chargement données RTE...")
    rte_pipeline = RTEDataPipeline(Path("data/Data_eCO2"), skiprows=3)
    df_rte = rte_pipeline.load_and_clean_rte()
    print(f"  Shape: {df_rte.shape}")
    print(f"  Colonnes: {df_rte.columns.tolist()}")
    
    # --- ÉTAPE 3: Fusion ---
    logger.info("\n[ÉTAPE 3] Fusion des données...")
    df_merged = DataFusionPipeline.merge_datasets(
        df_meteo, df_rte,
        meteo_date_col='date',
        rte_date_col='date',
        how='inner'
    )
    print(f"  Shape après fusion: {df_merged.shape}")
    
    # --- ÉTAPE 4: Nettoyage qualité ---
    logger.info("\n[ÉTAPE 4] Gestion de la qualité...")
    df_final = DataQualityPipeline.handle_missing_values(
        df_merged,
        numeric_interpolation='linear',
        categorical_fill='forward'
    )
    print(f"  Shape final: {df_final.shape}")
    
    # --- ÉTAPE 5: Analyse des outliers ---
    logger.info("\n[ÉTAPE 5] Détection outliers...")
    outliers = DataQualityPipeline.detect_and_report_outliers(df_final)
    if outliers:
        print(f"  Colonnes avec outliers: {list(outliers.keys())}")
    else:
        print(f"  Aucun outlier détecté")
    
    return df_final


# ============================================================================
# EXEMPLE 4: Configuration personnalisée
# ============================================================================
def example_custom_configuration():
    """
    Pipeline avec configuration entièrement personnalisée.
    
    Cas d'usage: Besoin d'ajuster l'interpolation, les seuils, etc.
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 4: Configuration Personnalisée")
    logger.info("=" * 80)
    
    # Créer une configuration custom
    config = PipelineConfig()
    
    # Modifier les paramètres de qualité
    config.quality.numeric_interpolation = 'polynomial'  # Polynomial au lieu de linear
    config.quality.interpolation_limit = 6               # Limite à 6 points
    config.quality.iqr_multiplier = 2.0                  # Outliers plus relâchés
    
    # Modifier les chemins
    config.meteo.data_dir = Path("data/Data_Climat")
    config.rte.data_dir = Path("data/Data_eCO2")
    config.output_dir = Path("output_custom")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Configuration personnalisée:")
    print(f"  Interpolation: {config.quality.numeric_interpolation}")
    print(f"  Limite interpolation: {config.quality.interpolation_limit}")
    print(f"  Seuil IQR: {config.quality.iqr_multiplier}")
    
    pipeline = EnergyDataPipeline(
        meteo_path=config.meteo.data_dir,
        rte_path=config.rte.data_dir,
        output_path=config.output_dir
    )
    
    df_final = pipeline.run(save_intermediate=True)
    return df_final


# ============================================================================
# EXEMPLE 5: Fusion partielle (un dept ou une période)
# ============================================================================
def example_partial_fusion():
    """
    Fusionner seulement certaines données.
    
    Cas d'usage: Tester sur un dept avant full pipeline.
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 5: Fusion Partielle (Filtrée)")
    logger.info("=" * 80)
    
    # Charger les données
    meteo_pipeline = MeteoDataPipeline(Path("data/Data_Climat"))
    df_meteo = meteo_pipeline.load_and_clean_meteo()
    
    rte_pipeline = RTEDataPipeline(Path("data/Data_eCO2"), skiprows=3)
    df_rte = rte_pipeline.load_and_clean_rte()
    
    # Filtrer Île-de-France (dept 75)
    logger.info("Filtrage sur département 75 (Île-de-France)...")
    df_meteo_filtered = df_meteo[df_meteo['code_dept'] == '75']
    
    print(f"Before: {df_meteo.shape[0]} rows")
    print(f"After filter: {df_meteo_filtered.shape[0]} rows")
    
    # Fusionner
    df_merged = DataFusionPipeline.merge_datasets(
        df_meteo_filtered, df_rte
    )
    
    # Nettoyer
    df_final = DataQualityPipeline.handle_missing_values(df_merged)
    
    logger.info(f"✓ Fusion partielle complétée: {df_final.shape}")
    return df_final


# ============================================================================
# EXEMPLE 6: Post-traitement et analyse
# ============================================================================
def example_post_analysis(df: pd.DataFrame):
    """
    Analyse post-pipeline.
    
    Après fusion et nettoyage, faire des analyses.
    """
    logger.info("=" * 80)
    logger.info("EXEMPLE 6: Analyse Post-Pipeline")
    logger.info("=" * 80)
    
    # Statiques descriptives
    print("\nStatistiques:")
    print(df.describe())
    
    # Covariance entre température et consommation
    if 'temperature' in df.columns and 'consommation' in df.columns:
        correlation = df['temperature'].corr(df['consommation'])
        print(f"\nCorrélation température/consommation: {correlation:.3f}")
    
    # Analyse par dept
    if 'code_dept' in df.columns:
        print(f"\nNombre de depts: {df['code_dept'].nunique()}")
        print(f"Depts présents: {sorted(df['code_dept'].unique())}")
    
    # Couverture temporelle
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        duration = df['date'].max() - df['date'].min()
        print(f"\nCouverture temporelle: {duration}")
        print(f"  De {df['date'].min()} à {df['date'].max()}")
    
    return df


# ============================================================================
# EXEMPLE 7: Pipeline réutilisable avec fonction wrapper
# ============================================================================
def run_pipeline_with_defaults(
    meteo_path: str = "data/Data_Climat",
    rte_path: str = "data/Data_eCO2",
    output_path: str = "output",
    config_preset: str = "default"
) -> pd.DataFrame:
    """
    Wrapper pour exécuter le pipeline facilement.
    
    Args:
        meteo_path: Chemin données météo
        rte_path: Chemin données RTE
        output_path: Chemin output
        config_preset: 'default', 'development', 'production'
    
    Returns:
        DataFrame final
    """
    if config_preset == 'production':
        config = ConfigPresets.production()
    elif config_preset == 'development':
        config = ConfigPresets.development()
    else:
        config = ConfigPresets.default()
    
    pipeline = EnergyDataPipeline(
        meteo_path=Path(meteo_path),
        rte_path=Path(rte_path),
        output_path=Path(output_path)
    )
    
    return pipeline.run(save_intermediate=(config_preset != 'production'))


# ============================================================================
# MAIN: Exécuter les exemples
# ============================================================================
if __name__ == "__main__":
    """
    Décommenter les exemples à exécuter.
    """
    
    # Exemple 1: Basic
    # df = example_basic_pipeline()
    
    # Exemple 2: Production
    # df = example_production_pipeline()
    
    # Exemple 3: Step by step
    # df = example_step_by_step()
    
    # Exemple 4: Custom
    # df = example_custom_configuration()
    
    # Exemple 5: Partial
    # df = example_partial_fusion()
    
    # Exemple 6: Post-analysis
    # df = run_pipeline_with_defaults()
    # example_post_analysis(df)
    
    # Exemple 7: Wrapper simple
    # df = run_pipeline_with_defaults(config_preset='production')
    
    print("\n✓ Tous les exemples sont disponibles!")
    print("Décommenter l'exemple à exécuter dans main.py")
