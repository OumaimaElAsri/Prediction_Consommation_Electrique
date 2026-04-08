import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_meteo_data(meteo_path: Path) -> pd.DataFrame:
    """Load and combine all meteorological CSV files"""
    csv_files = list(meteo_path.glob("*.csv"))
    logger.info(f"Trouvé {len(csv_files)} fichiers météorologiques")
    
    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file, sep=';')
        
        # Skip files without AAAAMMJJHH column (corrupted/different format)
        if 'AAAAMMJJHH' not in df.columns:
            logger.info(f"Skippé {csv_file.name}: colonne AAAAMMJJHH manquante")
            continue
            
        dept_code = csv_file.name.split('_')[1]  # H_75_latest -> 75
        df['code_dept'] = dept_code
        dfs.append(df)
        logger.info(f"Chargé {csv_file.name}: {df.shape[0]} lignes")
    
    df_meteo = pd.concat(dfs, ignore_index=True)
    logger.info(f"Météo finale: {df_meteo.shape}")
    
    # Créer colonne date depuis AAAAMMJJHH
    if 'AAAAMMJJHH' in df_meteo.columns:
        df_meteo['date'] = pd.to_datetime(df_meteo['AAAAMMJJHH'].astype(str), format='%Y%m%d%H')
        logger.info(f"Date range: {df_meteo['date'].min()} to {df_meteo['date'].max()}")
    
    return df_meteo


def load_rte_data(rte_path: Path) -> pd.DataFrame:
    """Load RTE energy data (TSV format despite .xls extension)"""
    xls_files = list(rte_path.glob("*.xls*"))
    logger.info(f"Trouvé {len(xls_files)} fichiers RTE")
    
    dfs = []
    for xls_file in xls_files:
        try:
            # These are actually TSV files, not Excel
            df = pd.read_csv(xls_file, sep='\t')
            # Clean: remove footer rows with text (like 'Délibération')
            df = df[~df.iloc[:, 0].astype(str).str.contains('Délibération|ensemble|L\'', case=False, na=False)]
            dfs.append(df)
            logger.info(f"Chargé {xls_file.name}: {df.shape[0]} lignes valides")
        except Exception as e:
            logger.warning(f"Erreur {xls_file.name}: {e}")
            continue
    
    if not dfs:
        logger.error("Aucun fichier RTE chargé avec succès!")
        return pd.DataFrame()
    
    df_rte = pd.concat(dfs, ignore_index=True)
    logger.info(f"RTE final (avant nettoyage): {df_rte.shape}")
    
    # Normaliser noms colonnes
    df_rte.columns = df_rte.columns.str.lower().str.strip()
    
    # Trouver colonne date
    date_cols = [c for c in df_rte.columns if 'date' in c.lower()]
    if date_cols:
        df_rte['date'] = pd.to_datetime(df_rte[date_cols[0]], errors='coerce')
        # Remove rows with invalid dates
        df_rte = df_rte.dropna(subset=['date'])
        logger.info(f"RTE après nettoyage: {df_rte.shape}")
    else:
        df_rte['date'] = pd.date_range(start='2025-01-01', periods=len(df_rte), freq='D')
    
    # Garder que les colonnes importantes
    important_cols = ['date', 'type de jour tempo', 'consommation_mwh'] if 'consommation_mwh' in df_rte.columns else ['date', 'type de jour tempo']
    for col in important_cols:
        if col not in df_rte.columns and col != 'consommation_mwh':
            continue
    
    return df_rte[['date'] + [c for c in df_rte.columns if c != 'date']]


def merge_datasets(df_meteo: pd.DataFrame, df_rte: pd.DataFrame) -> pd.DataFrame:
    """Merge meteorological and RTE data"""
    logger.info(f"Fusion:\n  Météo: {df_meteo.shape[0]} lignes\n  RTE: {df_rte.shape[0]} lignes")
    
    # Normaliser dates
    df_meteo['date'] = pd.to_datetime(df_meteo['date']).dt.normalize()  # Remove time
    df_rte['date'] = pd.to_datetime(df_rte['date']).dt.normalize()  # Remove time
    
    # Agréger météo par date (moyenne pour colonnes numériques)
    agg_dict = {}
    for col in df_meteo.columns:
        if col != 'date' and df_meteo[col].dtype in [np.float64, np.int64]:
            agg_dict[col] = 'mean'
        elif col == 'code_dept':
            agg_dict[col] = 'first'
    
    df_meteo_daily = df_meteo.groupby('date', as_index=False).agg(agg_dict)
    logger.info(f"Météo agrégée: {df_meteo_daily.shape}")
    
    # Merge LEFT: garder tous les jours RTE
    df_merged = pd.merge(df_rte, df_meteo_daily, on='date', how='left')
    
    logger.info(f"Résultat fusion: {df_merged.shape}")
    return df_merged


def main():
    meteo_path = Path("data/Data_Climat")
    rte_path = Path("data/Data_eCO2")
    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    
    # Charger
    df_meteo = load_meteo_data(meteo_path)
    df_rte = load_rte_data(rte_path)
    
    # Fusionner
    df_final = merge_datasets(df_meteo, df_rte)
    
    # Sauvegarder
    df_final.to_csv(output_path / "dataset_final_clean.csv", index=False)
    df_final.to_parquet(output_path / "dataset_final_clean.parquet", compression='snappy', index=False)
    
    logger.info(f"Données sauvegardées: {output_path}")
    print("\nRésumé:")
    print(f"  Lignes: {df_final.shape[0]}")
    print(f"  Colonnes: {df_final.shape[1]}")
    print(f"  Valeurs nulles: {df_final.isnull().sum().sum()}")
    print(f"  Colonnes: {list(df_final.columns)}")


if __name__ == "__main__":
    main()
