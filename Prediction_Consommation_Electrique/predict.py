#!/usr/bin/env python3
"""
Pipeline de Prédiction Énergétique - Point d'Entrée Principal

Exécute le pipeline complet:
1. Data Cleaning (merger météo + RTE)
2. Feature Engineering (calendaires, lag, interaction)
3. Modeling (XGBoost avec séparation temporelle)
4. Export (processed_data.csv)

Utilisation:
    python predict.py                    # Exécution complète
    python predict.py --help             # Aide

Author: Senior Data Scientist
Created: 2026-04-03
"""

import argparse
import sys
import os
from pathlib import Path

# Force UTF-8 encoding for output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scripts.prediction_pipeline import PredictionPipeline

# Déterminer le répertoire de base du script
SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    """Fonction principale."""
    
    # Définir les chemins par défaut relatifs au répertoire du script
    default_meteo = SCRIPT_DIR / "data" / "Data_Climat"
    default_rte = SCRIPT_DIR / "data" / "Data_eCO2"
    default_output = SCRIPT_DIR / "output"
    default_output_file = SCRIPT_DIR / "data" / "processed_data.csv"
    
    parser = argparse.ArgumentParser(
        description="Pipeline End-to-End de prédiction de consommation électrique"
    )
    parser.add_argument(
        '--meteo-path',
        type=Path,
        default=default_meteo,
        help="Chemin du répertoire Data_Climat"
    )
    parser.add_argument(
        '--rte-path',
        type=Path,
        default=default_rte,
        help="Chemin du répertoire Data_eCO2"
    )
    parser.add_argument(
        '--output-path',
        type=Path,
        default=default_output,
        help="Répertoire output"
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        default=default_output_file,
        help="Fichier de sortie final (processed_data.csv)"
    )
    
    # Change le répertoire de travail au répertoire du script si nécessaire
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)
        print(f"Répertoire de travail changé à: {SCRIPT_DIR}")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("PIPELINE DE PRÉDICTION ÉNERGÉTIQUE EN FRANCE")
    print("=" * 80)
    print(f"\nChemins:")
    print(f"  Météo: {args.meteo_path}")
    print(f"  RTE: {args.rte_path}")
    print(f"  Output: {args.output_path}")
    print(f"  Fichier final: {args.output_file}\n")
    
    # Créer et exécuter le pipeline
    pipeline = PredictionPipeline(
        meteo_path=args.meteo_path,
        rte_path=args.rte_path,
        output_path=args.output_path,
        data_processed_path=args.output_file
    )
    
    try:
        dataset_final, results = pipeline.run()
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE EXÉCUTÉ AVEC SUCCÈS")
        print("=" * 80)
        print(f"\nRésultat final sauvegardé dans: {args.output_file}")
        print(f"Affichage des premières lignes:")
        print(dataset_final.head())
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
