#!/usr/bin/env python3
"""
Script principal pour exécuter le pipeline complet de prédiction énergétique.

Utilisation:
    python main.py                              # Exécution par défaut
    python main.py --config production          # Avec preset production
    python main.py --config development         # Avec preset development
    python main.py --verbose                    # Mode verbose
    python main.py --no-intermediate            # Sans fichiers intermédiaires

Author: Data Engineering Team
Created: 2026-04-03
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

from scripts.data_pipeline import EnergyDataPipeline
from scripts.config import ConfigPresets, DEFAULT_CONFIG

# Déterminer le répertoire de base du script
SCRIPT_DIR = Path(__file__).resolve().parent


def setup_logging(log_level: str, logs_dir: Path) -> logging.Logger:
    """
    Configure le système de logging.
    
    Args:
        log_level: Niveau de logging (INFO, DEBUG, WARNING, ERROR)
        logs_dir: Répertoire pour stocker les fichiers de log
    
    Returns:
        Logger configuré
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Fichier de log: {log_file}")
    
    return logger


def main():
    """Fonction principale du pipeline."""
    
    # Change le répertoire de travail au répertoire du script si nécessaire
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Pipeline de nettoyage et fusion de données énergétiques"
    )
    parser.add_argument(
        '--config',
        choices=['default', 'development', 'production'],
        default='default',
        help="Profile de configuration à utiliser"
    )
    parser.add_argument(
        '--meteo-path',
        type=Path,
        help="Chemin du répertoire Data_Climat"
    )
    parser.add_argument(
        '--rte-path',
        type=Path,
        help="Chemin du répertoire Data_eCO2"
    )
    parser.add_argument(
        '--output-path',
        type=Path,
        help="Chemin du répertoire de sortie"
    )
    parser.add_argument(
        '--meteo-date-col',
        default='date',
        help="Nom de la colonne temporelle dans les données météo"
    )
    parser.add_argument(
        '--rte-date-col',
        default='date',
        help="Nom de la colonne temporelle dans les données RTE"
    )
    parser.add_argument(
        '--no-intermediate',
        action='store_true',
        help="Ne pas sauvegarder les fichiers intermédiaires"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Mode verbose"
    )
    parser.add_argument(
        '--output-format',
        choices=['csv', 'parquet', 'both'],
        default='both',
        help="Format de sortie du dataset final"
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    if args.config == 'development':
        config = ConfigPresets.development()
    elif args.config == 'production':
        config = ConfigPresets.production()
    else:
        config = DEFAULT_CONFIG
    
    # Override avec arguments de ligne de commande
    if args.meteo_path:
        config.meteo.data_dir = args.meteo_path
    if args.rte_path:
        config.rte.data_dir = args.rte_path
    if args.output_path:
        config.output_dir = args.output_path
    
    config.save_intermediate = not args.no_intermediate
    config.verbose = args.verbose
    config.output_format = args.output_format
    
    # Setup logging
    logger = setup_logging(config.log_level, config.logs_dir)
    
    logger.info("=" * 80)
    logger.info("DÉMARRAGE DU PIPELINE DE PRÉDICTION ÉNERGÉTIQUE")
    logger.info("=" * 80)
    logger.info(f"Configuration: {args.config}")
    logger.info(f"Chemin météo: {config.meteo.data_dir}")
    logger.info(f"Chemin RTE: {config.rte.data_dir}")
    logger.info(f"Chemin output: {config.output_dir}")
    
    try:
        # Créer et exécuter le pipeline
        pipeline = EnergyDataPipeline(
            meteo_path=config.meteo.data_dir,
            rte_path=config.rte.data_dir,
            output_path=config.output_dir
        )
        
        df_final = pipeline.run(
            meteo_date_col=args.meteo_date_col,
            rte_date_col=args.rte_date_col,
            save_intermediate=config.save_intermediate
        )
        
        # Sauvegarder le résultat final
        logger.info(f"\nSauvegarde du dataset final...")
        
        if config.output_format in ['csv', 'both']:
            output_csv = config.output_dir / "dataset_final_clean.csv"
            df_final.to_csv(output_csv, index=False)
            logger.info(f"✓ CSV sauvegardé: {output_csv}")
        
        if config.output_format in ['parquet', 'both']:
            output_parquet = config.output_dir / "dataset_final_clean.parquet"
            df_final.to_parquet(
                output_parquet,
                compression=config.parquet_compression,
                index=False
            )
            logger.info(f"✓ Parquet sauvegardé: {output_parquet}")
        
        # Résumé final
        logger.info("\n" + "=" * 80)
        logger.info("✓ PIPELINE EXÉCUTÉ AVEC SUCCÈS")
        logger.info("=" * 80)
        logger.info(f"Dimensions du dataset final: {df_final.shape}")
        logger.info(f"Colonnes: {df_final.columns.tolist()}")
        logger.info(f"Mémoire utilisée: {df_final.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Pipeline interrompu par l'utilisateur")
        return 1
    
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
