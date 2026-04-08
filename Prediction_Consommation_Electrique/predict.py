#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from scripts.prediction_pipeline import PredictionPipeline

SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)
    
    parser = argparse.ArgumentParser(description="Energy prediction pipeline")
    parser.add_argument('--meteo-path', type=Path, default=SCRIPT_DIR / "data" / "Data_Climat")
    parser.add_argument('--rte-path', type=Path, default=SCRIPT_DIR / "data" / "Data_eCO2")
    parser.add_argument('--output-path', type=Path, default=SCRIPT_DIR / "output")
    parser.add_argument('--output-file', type=Path, default=SCRIPT_DIR / "output" / "predictions.csv")
    
    args = parser.parse_args()
    
    print(f"Meteo: {args.meteo_path}")
    print(f"RTE: {args.rte_path}")
    print(f"Output: {args.output_path}\n")
    
    pipeline = PredictionPipeline(
        meteo_path=args.meteo_path,
        rte_path=args.rte_path,
        output_path=args.output_path,
        data_processed_path=args.output_file
    )
    
    try:
        dataset_final, results = pipeline.run()
        print(f"Done. Shape: {dataset_final.shape}")
        print(f"Output saved to: {args.output_file}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
