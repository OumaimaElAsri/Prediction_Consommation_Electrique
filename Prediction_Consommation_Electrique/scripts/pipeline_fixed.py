#!/usr/bin/env python3
"""Fixed data pipeline: Merge meteorological data with RTE TEMPO calendar"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_meteo_data(meteo_path: Path) -> pd.DataFrame:
    """Load and combine all meteorological CSV files, daily aggregation"""
    csv_files = list(meteo_path.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} meteorological files")
    
    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file, sep=';')
        
        # Skip files without AAAAMMJJHH column
        if 'AAAAMMJJHH' not in df.columns:
            logger.info(f"Skipped {csv_file.name}: missing AAAAMMJJHH column")
            continue
            
        dept_code = csv_file.name.split('_')[1]
        df['code_dept'] = dept_code
        dfs.append(df)
        logger.info(f"Loaded {csv_file.name}: {len(df)} rows")
    
    df_meteo = pd.concat(dfs, ignore_index=True)
    logger.info(f"Final meteorological data: {df_meteo.shape}")
    
    # Convert time to datetime and normalize to date only
    df_meteo['date'] = pd.to_datetime(df_meteo['AAAAMMJJHH'].astype(str), format='%Y%m%d%H')
    df_meteo['date'] = df_meteo['date'].dt.normalize()  # Remove time, keep date only
    
    # Daily aggregation (mean for all numeric columns)
    numeric_cols = df_meteo.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != 'AAAAMMJJHH']
    
    agg_dict = {col: 'mean' for col in numeric_cols}
    agg_dict['code_dept'] = 'first'
    
    df_daily = df_meteo.groupby('date', as_index=False).agg(agg_dict)
    
    logger.info(f"Daily meteorological data: {df_daily.shape}")
    logger.info(f"Date range: {df_daily['date'].min()} to {df_daily['date'].max()}")
    
    return df_daily


def load_rte_data(rte_path: Path) -> pd.DataFrame:
    """Load RTE TEMPO calendar data"""
    xls_files = list(rte_path.glob("*.xls*"))
    logger.info(f"Found {len(xls_files)} RTE files")
    
    dfs = []
    for xls_file in xls_files:
        try:
            # Read TSV despite .xls extension
            df = pd.read_csv(xls_file, sep='\t')
            
            # Clean: remove footer text rows
            df = df[~df.iloc[:, 0].astype(str).str.contains('Délibération|ensemble|L\'', case=False, na=False)]
            
            # Parse dates
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            
            dfs.append(df)
            logger.info(f"Loaded {xls_file.name}: {len(df)} valid rows")
        except Exception as e:
            logger.warning(f"Error {xls_file.name}: {e}")
            continue
    
    if not dfs:
        logger.error("No RTE files loaded!")
        return pd.DataFrame()
    
    df_rte = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['Date'])
    
    # Normalize column names
    df_rte.columns = df_rte.columns.str.lower().str.strip()
    df_rte = df_rte.rename(columns={'date': 'date', 'type de jour tempo': 'type_jour_tempo'})
    
    logger.info(f"Final RTE data: {df_rte.shape}")
    logger.info(f"Date range: {df_rte['date'].min()} to {df_rte['date'].max()}")
    
    return df_rte[['date', 'type_jour_tempo']].copy()


def merge_datasets(df_meteo: pd.DataFrame, df_rte: pd.DataFrame) -> pd.DataFrame:
    """Merge meteorological and RTE data on date"""
    logger.info(f"Merging:\n  Meteorology: {df_meteo.shape}\n  RTE: {df_rte.shape}")
    
    # Normalize dates (remove time part)
    df_meteo['date'] = pd.to_datetime(df_meteo['date']).dt.normalize()
    df_rte['date'] = pd.to_datetime(df_rte['date']).dt.normalize()
    
    # LEFT join on RTE dates (keep all RTE days)
    df_merged = pd.merge(df_rte, df_meteo, on='date', how='left')
    
    logger.info(f"Merge result: {df_merged.shape}")
    logger.info(f"Rows with meteorological data: {df_merged.notna().sum().sum() - len(df_merged)}")
    
    return df_merged


def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save merged data"""
    output_path.mkdir(exist_ok=True)
    
    # CSV
    csv_file = output_path / 'dataset_final.csv'
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved: {csv_file}")
    
    # Parquet
    parquet_file = output_path / 'dataset_final.parquet'
    df.to_parquet(parquet_file, index=False)
    logger.info(f"Saved: {parquet_file}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Missing values (total): {df.isnull().sum().sum()}")
    
    # Column breakdown
    print(f"\nColumns with data:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        pct = 100 * non_null / len(df)
        print(f"  {col}: {non_null}/{len(df)} ({pct:.1f}%)")


def main():
    meteo_path = Path("data/Data_Climat")
    rte_path = Path("data/Data_eCO2")
    output_path = Path("output")
    
    logger.info("="*60)
    logger.info("FIXED DATA PIPELINE: Meteorology + RTE TEMPO")
    logger.info("="*60)
    
    # Load and process
    df_meteo = load_meteo_data(meteo_path)
    df_rte = load_rte_data(rte_path)
    
    # Merge
    df_final = merge_datasets(df_meteo, df_rte)
    
    # Save
    save_data(df_final, output_path)
    
    logger.info("="*60)
    logger.info("Pipeline completed successfully!")


if __name__ == '__main__':
    main()
