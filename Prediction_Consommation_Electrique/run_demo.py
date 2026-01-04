#!/usr/bin/env python3
"""
Script DÉMO: Pipeline End-to-End avec données de test uniquement

Ceci est une démonstration du pipeline complet utilisant uniquement les données de test
générées (H_13, H_69, H_75 + RTE test data), ce qui permet une exécution rapide sans
problèmes de mémoire.

Utilisation:
    python run_demo.py                  # Exécute le pipeline de démo
    python run_demo.py --verbose        # Mode verbose

Author: Data Engineering Team
Created: 2026-04-05
"""

import argparse
import sys
import os
import shutil
from pathlib import Path
import logging

# Force UTF-8 encoding for output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Déterminer le répertoire de base
SCRIPT_DIR = Path(__file__).resolve().parent

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_demo_environment():
    """Crée un environnement de démo avec seulement les données de test."""
    
    logger.info("=" * 80)
    logger.info("PRÉPARATION ENVIRONNEMENT DÉMO")
    logger.info("=" * 80)
    
    data_dir = SCRIPT_DIR / "data"
    meteo_dir = data_dir / "Data_Climat"
    rte_dir = data_dir / "Data_eCO2"
    
    # Créer répertoire démo
    demo_dir = SCRIPT_DIR / "data_demo"
    demo_meteo = demo_dir / "Data_Climat_Demo"
    demo_rte = demo_dir / "Data_eCO2_Demo"
    
    demo_dir.mkdir(exist_ok=True)
    demo_meteo.mkdir(exist_ok=True, parents=True)
    demo_rte.mkdir(exist_ok=True, parents=True)
    
    logger.info(f"\nRépertoire démo: {demo_dir}")
    
    # Copier UNIQUEMENT les fichiers de test
    test_files_meteo = ['H_13_latest-2025-2026.csv', 'H_69_latest-2025-2026.csv', 'H_75_latest-2025-2026.csv']
    test_files_rte = ['eCO2mix_RTE_tempo_2025-2026.csv']
    
    logger.info("\n📋 Fichiers météo de test à copier:")
    for file in test_files_meteo:
        src = meteo_dir / file
        dst = demo_meteo / file
        if src.exists():
            shutil.copy2(src, dst)
            logger.info(f"  ✓ {file}")
        else:
            logger.warning(f"  ✗ {file} introuvable")
    
    logger.info("\n📋 Fichiers RTE de test à copier:")
    for file in test_files_rte:
        src = rte_dir / file
        dst = demo_rte / file
        if src.exists():
            shutil.copy2(src, dst)
            logger.info(f"  ✓ {file}")
        else:
            logger.warning(f"  ✗ {file} introuvable")
    
    return demo_meteo, demo_rte


def main():
    """Fonction principale."""
    
    # Change le répertoire de travail
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)
    
    parser = argparse.ArgumentParser(
        description="Démonstration du pipeline avec données de test"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Mode verbose"
    )
    parser.add_argument(
        '--keep-demo-data',
        action='store_true',
        help="Conserver les données de démo après exécution"
    )
    
    args = parser.parse_args()
    
    # Configurer logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "=" * 80)
    print("DÉMO PIPELINE: PRÉDICTION CONSOMMATION ÉLECTRIQUE")
    print("=" * 80)
    print("\nCette démonstration exécute le pipeline complet avec des données de test")
    print("pour montrer toutes les étapes sans problèmes de mémoire.\n")
    
    try:
        # Préparer l'environnement de démo
        demo_meteo, demo_rte = setup_demo_environment()
        
        # Importer le pipeline
        from scripts.prediction_pipeline import PredictionPipeline
        
        logger.info("\n" + "=" * 80)
        logger.info("EXÉCUTION DU PIPELINE COMPLET")
        logger.info("=" * 80 + "\n")
        
        # Exécuter le pipeline
        pipeline = PredictionPipeline(
            meteo_path=demo_meteo,
            rte_path=demo_rte,
            output_path=SCRIPT_DIR / "output_demo",
            data_processed_path=SCRIPT_DIR / "data" / "processed_data_demo.csv"
        )
        
        dataset_final, results = pipeline.run()
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE EXÉCUTÉ AVEC SUCCÈS")
        print("=" * 80)
        print(f"\n📊 Résultats:")
        print(f"  - Lignes: {dataset_final.shape[0]}")
        print(f"  - Colonnes: {dataset_final.shape[1]}")
        print(f"\n📁 Fichier final: {SCRIPT_DIR / 'data' / 'processed_data_demo.csv'}")
        print(f"\n📊 Aperçu des données (5 premières lignes):")
        print(dataset_final.head())
        
        print("\n✨ Démonstration complète! ✨\n")
        
        # Nettoyer les données de démo si demandé
        if not args.keep_demo_data:
            logger.info("\nNettoyage des données de démo...")
            import shutil
            demo_dir = SCRIPT_DIR / "data_demo"
            if demo_dir.exists():
                shutil.rmtree(demo_dir)
                logger.info("✓ Données de démo supprimées")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
