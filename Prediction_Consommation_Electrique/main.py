#!/usr/bin/env python3

import argparse
import logging
import os
from pathlib import Path
from datetime import datetime

from scripts.data_pipeline import EnergyDataPipeline
from scripts.config import ConfigPresets, DEFAULT_CONFIG

SCRIPT_DIR = Path(__file__).resolve().parent


def setup_logging(log_level, logs_dir):
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
    return logging.getLogger(__name__)


def main():
    if Path.cwd() != SCRIPT_DIR:
        os.chdir(SCRIPT_DIR)
    
    parser = argparse.ArgumentParser(description="Energy prediction pipeline")
    parser.add_argument('--config', choices=['default', 'development', 'production'], default='default')
    parser.add_argument('--meteo-path', type=Path)
    parser.add_argument('--rte-path', type=Path)
    parser.add_argument('--output-path', type=Path)
    parser.add_argument('--no-intermediate', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--output-format', choices=['csv', 'parquet', 'both'], default='both')
    args = parser.parse_args()
    
    if args.config == 'development':
        config = ConfigPresets.development()
    elif args.config == 'production':
        config = ConfigPresets.production()
    else:
        config = DEFAULT_CONFIG
    
    if args.meteo_path:
        config.meteo.data_dir = args.meteo_path
    if args.rte_path:
        config.rte.data_dir = args.rte_path
    if args.output_path:
        config.output_dir = args.output_path
    
    config.save_intermediate = not args.no_intermediate
    config.verbose = args.verbose
    config.output_format = args.output_format
    
    logger = setup_logging(config.log_level, config.logs_dir)
    
    logger.info("Starting energy prediction pipeline")
    logger.info(f"Config: {args.config}")
    logger.info(f"Meteo path: {config.meteo.data_dir}")
    logger.info(f"RTE path: {config.rte.data_dir}")
    logger.info(f"Output: {config.output_dir}")
    
    try:
        pipeline = EnergyDataPipeline(
            meteo_path=config.meteo.data_dir,
            rte_path=config.rte.data_dir,
            output_path=config.output_dir
        )
        
        df_final = pipeline.run(save_intermediate=config.save_intermediate)
        
        if config.output_format in ['csv', 'both']:
            output_csv = config.output_dir / "dataset_final_clean.csv"
            df_final.to_csv(output_csv, index=False)
            logger.info(f"CSV saved: {output_csv}")
        
        if config.output_format in ['parquet', 'both']:
            output_parquet = config.output_dir / "dataset_final_clean.parquet"
            df_final.to_parquet(output_parquet, compression='snappy', index=False)
            logger.info(f"Parquet saved: {output_parquet}")
        
        logger.info(f"Done. Shape: {df_final.shape}")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
