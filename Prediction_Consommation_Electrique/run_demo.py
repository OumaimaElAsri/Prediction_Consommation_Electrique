#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
import logging

SCRIPT_DIR = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_demo_environment():
    logger.info("Setting up demo environment...")
    
    data_dir = SCRIPT_DIR / "data"
    meteo_dir = data_dir / "Data_Climat"
    rte_dir = data_dir / "Data_eCO2"
    
    demo_dir = SCRIPT_DIR / "data_demo"
    demo_meteo = demo_dir / "Data_Climat_Demo"
    demo_rte = demo_dir / "Data_eCO2_Demo"
    
    demo_dir.mkdir(exist_ok=True)
    demo_meteo.mkdir(exist_ok=True, parents=True)
    demo_rte.mkdir(exist_ok=True, parents=True)
    
    logger.info(f"Demo directory: {demo_dir}")
    
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
