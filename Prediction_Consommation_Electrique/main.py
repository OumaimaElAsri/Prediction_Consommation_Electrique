#!/usr/bin/env python3

import argparse
import logging
import os
from pathlib import Path
import pandas as pd
from scripts.data_pipeline import EnergyDataPipeline
from scripts.feature_engineering import create_feature_dataset
from scripts.modeling import run_complete_modeling_pipeline

SCRIPT_DIR = Path(__file__).resolve().parent

def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("pipeline")


def main():
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)

    parser = argparse.ArgumentParser(description="Pipeline prediction consommation electrique")
    parser.add_argument("--meteo-path", type=Path, default=SCRIPT_DIR / "data" / "Data_Climat")
    parser.add_argument("--rte-path", type=Path, default=SCRIPT_DIR / "data" / "Data_eCO2")
    parser.add_argument("--output-path", type=Path, default=SCRIPT_DIR / "output")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["prepare", "train_predict", "full"],
        default="full",
        help="prepare: dataset nettoye, train_predict: modele sur dataset existant, full: pipeline complet",
    )
    args = parser.parse_args()

    logger = setup_logging(args.verbose)
    output_dir = Path(args.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        dataset_file = output_dir / "dataset_final_clean.csv"

        if args.mode in {"prepare", "full"}:
            pipeline = EnergyDataPipeline(args.meteo_path, args.rte_path, output_dir)
            df_clean = pipeline.run(save_intermediate=False)
            df_clean.to_csv(dataset_file, index=False)
            logger.info("Saved cleaned dataset: %s", dataset_file)

        if args.mode in {"train_predict", "full"}:
            if not dataset_file.exists():
                raise FileNotFoundError(
                    f"{dataset_file} introuvable. Lance d'abord --mode prepare ou --mode full."
                )
            df_clean = create_feature_dataset(pd.read_csv(dataset_file), None)
            predictions_df, _ = run_complete_modeling_pipeline(df_clean, output_dir)
            predictions_df.to_csv(output_dir / "predictions.csv", index=False)
            logger.info("Saved predictions: %s", output_dir / "predictions.csv")
            logger.info("Saved feature importance: %s", output_dir / "feature_importance.csv")

        logger.info("Pipeline termine. Sorties principales dans %s", output_dir)
        return 0
    except Exception as e:
        logger.error("Erreur pipeline: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
