"""
Module pour le nettoyage des données
"""

import pandas as pd
import numpy as np
from .utils import logger

def load_and_clean_data(filepath, **kwargs):
    """
    Charge et nettoie les données brutes
    
    Parameters:
    -----------
    filepath : str
        Chemin vers le fichier de données
    **kwargs : dict
        Arguments additionnels pour pd.read_csv()
    
    Returns:
    --------
    pd.DataFrame
        DataFrame nettoyé
    """
    # Charger les données
    df = pd.read_csv(filepath, **kwargs)
    logger.info(f"Fichier chargé: {filepath}")
    logger.info(f"Dimensions initiales: {df.shape}")
    
    # Nettoyer
    df = remove_duplicates(df)
    df = handle_missing_values(df)
    df = remove_outliers(df)
    
    logger.info(f"Dimensions après nettoyage: {df.shape}")
    return df

def remove_duplicates(df):
    """Supprime les doublons"""
    initial_rows = len(df)
    df = df.drop_duplicates()
    removed = initial_rows - len(df)
    if removed > 0:
        logger.info(f"Doublons supprimés: {removed}")
    return df

def handle_missing_values(df, strategy='drop'):
    """
    Gère les valeurs manquantes
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame d'entrée
    strategy : str
        'drop' : supprime les lignes avec valeurs manquantes
        'mean' : remplace par la moyenne (colonnes numériques)
    """
    missing = df.isnull().sum()
    if missing.sum() > 0:
        logger.info(f"Valeurs manquantes trouvées:\n{missing[missing > 0]}")
        
        if strategy == 'drop':
            df = df.dropna()
        elif strategy == 'mean':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    
    return df

def remove_outliers(df, method='iqr', threshold=1.5):
    """
    Supprime les valeurs aberrantes
    
    Parameters:
    -----------
    df : pd.DataFrame
    method : str
        'iqr' : utilise la méthode de l'écart interquartile
    threshold : float
        Multiplicateur pour l'écart interquartile
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if method == 'iqr':
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > 0:
                logger.info(f"Valeurs aberrantes trouvées dans {col}: {len(outliers)}")
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    
    return df
