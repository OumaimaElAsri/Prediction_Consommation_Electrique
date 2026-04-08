import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from .utils import logger


def preprocess_data(df, scale=True, scaler_type='standard'):
    df = df.copy()
    df = convert_data_types(df)
    df = create_temporal_features(df)
    if scale:
        df = scale_features(df, scaler_type=scaler_type)
    logger.info("Prétraitement terminé")
    return df


def convert_data_types(df):
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                logger.info(f"Colonne {col} convertie en datetime")
            except:
                pass
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].nunique() < 20:
            df[col] = df[col].astype('category')
    return df


def create_temporal_features(df):
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    for col in datetime_cols:
        df[f'{col}_year'] = df[col].dt.year
        df[f'{col}_month'] = df[col].dt.month
        df[f'{col}_day'] = df[col].dt.day
        df[f'{col}_dayofweek'] = df[col].dt.dayofweek
        logger.info(f"Features temporelles créées pour {col}")
    return df


def scale_features(df, scaler_type='standard'):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if scaler_type == 'standard':
        scaler = StandardScaler()
    elif scaler_type == 'minmax':
        scaler = MinMaxScaler()
    else:
        logger.warning(f"Type de scaler inconnu: {scaler_type}")
        return df
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    logger.info(f"Normalisation {scaler_type} appliquée")
    return df


def encode_categorical(df, method='onehot'):
    categorical_cols = df.select_dtypes(include=['category']).columns.tolist()
    if method == 'onehot':
        df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
        logger.info(f"One-Hot Encoding appliqué: {categorical_cols}")
    return df

