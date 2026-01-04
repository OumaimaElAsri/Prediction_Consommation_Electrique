"""
Module de modélisation prédictive pour la consommation électrique.

Utilise XGBoost pour prédire la consommation avec :
- Séparation temporelle stricte (pas de data leakage)
- Train: 2024-2025, Test: 2025-2026
- Validation: Split chronologique
- Hyperparamètres optimisés pour séries temporelles

Author: Senior Data Scientist
Created: 2026-04-03
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, List
from datetime import datetime
import logging

import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configuration du logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TemporalModelingPipeline:
    """Pipeline de modélisation avec séparation temporelle."""
    
    def __init__(self, 
                 df: pd.DataFrame,
                 target_col: str = 'consommation_mwh',
                 date_col: str = 'date',
                 train_end_date: str = '2025-06-30',
                 test_start_date: str = '2025-07-01'):
        """
        Initialise le pipeline de modélisation.
        
        IMPORTANT: Séparation temporelle stricte pour éviter data leakage!
        
        Args:
            df: DataFrame avec features
            target_col: Colonne cible à prédire
            date_col: Colonne date
            train_end_date: Date de fin de l'ensemble d'entraînement
            test_start_date: Date de début de l'ensemble de test
        """
        self.df = df.copy()
        self.df[date_col] = pd.to_datetime(self.df[date_col])
        
        self.target_col = target_col
        self.date_col = date_col
        self.train_end_date = pd.to_datetime(train_end_date)
        self.test_start_date = pd.to_datetime(test_start_date)
        
        self.model = None
        self.scaler = None
        self.feature_importance = None
        self.predictions = None
        
        logger.info(f"Pipeline modélisation initialisé")
        logger.info(f"  Train: jusqu'à {self.train_end_date.date()}")
        logger.info(f"  Test: à partir de {self.test_start_date.date()}")
    
    def temporal_train_test_split(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Divise les données de manière chronologique (STRICTE).
        
        RATIONALE:
        ==========
        Problème: Les modèles ML standards mélangent les dates dans train/test
        Solution: Séparation TEMPORELLE stricte
        
        Structure:
        - TRAIN: avant 2025-06-30 (données complètes)
        - VAL: 2025-07-01 à 2025-11-30 (monitoring early stopping)
        - TEST: 2025-12-01+ (évaluation future)
        
        Avantages:
        ✓ Pas de data leakage (future ≠ past)
        ✓ Simule vraie prediction task
        ✓ Évite overfitting sur patterns temporels
        
        Returns:
            Tuple (train_df, val_df, test_df)
        """
        logger.info("\n" + "="*80)
        logger.info("SÉPARATION TEMPORELLE - STRICTE")
        logger.info("="*80)
        
        # Trier par date
        df_sorted = self.df.sort_values(self.date_col).reset_index(drop=True)
        
        # Définir les dates de split
        val_start = self.train_end_date + pd.Timedelta(days=1)
        val_end = pd.to_datetime('2025-11-30')
        test_start = pd.to_datetime('2025-12-01')
        
        # Split
        train_df = df_sorted[df_sorted[self.date_col] <= self.train_end_date].copy()
        val_df = df_sorted[(df_sorted[self.date_col] >= val_start) & 
                          (df_sorted[self.date_col] <= val_end)].copy()
        test_df = df_sorted[df_sorted[self.date_col] >= test_start].copy()
        
        logger.info(f"\nTRAIN set: {len(train_df)} lignes ({train_df[self.date_col].min().date()} à {train_df[self.date_col].max().date()})")
        logger.info(f"VAL set: {len(val_df)} lignes ({val_df[self.date_col].min().date()} à {val_df[self.date_col].max().date()})")
        logger.info(f"TEST set: {len(test_df)} lignes ({test_df[self.date_col].min().date()} à {test_df[self.date_col].max().date()})")
        
        total = len(train_df) + len(val_df) + len(test_df)
        logger.info(f"\nRépartition:")
        logger.info(f"  Train: {len(train_df)/total*100:.1f}%")
        logger.info(f"  Val: {len(val_df)/total*100:.1f}%")
        logger.info(f"  Test: {len(test_df)/total*100:.1f}%")
        
        return train_df, val_df, test_df
    
    def prepare_features(self, df: pd.DataFrame, feature_names: Optional[List[str]] = None) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Prépare les features et la cible.
        
        Exclus:
        - Colonnes temporelles (date)
        - Colonne cible
        - Features avec trop de NaN
        
        Args:
            df: DataFrame à préparer
            feature_names: Liste des noms de features à utiliser (si None, les sélectionner automatiquement)
        
        Returns:
            Tuple (X, y, feature_names)
        """
        df = df.copy()
        
        # Cible
        y = df[self.target_col].values
        
        if feature_names is None:
            # Features: Tout sauf date et cible, SEULEMENT colonnes numériques
            exclude_cols = {self.date_col, self.target_col, 'code_dept', 'region', 'type de jour tempo', 'NOM_USUEL'}
            
            # Garder seulement les colonnes numériques
            numeric_df = df.select_dtypes(include=['number'])
            feature_names = [col for col in numeric_df.columns if col not in exclude_cols]
            
            # Supprimer colonnes avec trop de NaN
            feature_names = [col for col in feature_names if df[col].isnull().sum() / len(df) < 0.1]
        
        # Remplir les NaN avec la médiane (plus robuste que la moyenne)
        X = df[feature_names].fillna(df[feature_names].median()).values
        
        logger.info(f"Features utilisées: {len(feature_names)}")
        logger.info(f"  {feature_names[:10]}...")  # Afficher seulement les 10 premiers
        
        return X, y, feature_names
    
    def train_model(self, 
                   train_df: pd.DataFrame,
                   val_df: pd.DataFrame,
                   hyperparams: Optional[Dict] = None) -> Dict:
        """
        Entraîne le modèle XGBoost.
        
        Hyperparamètres optimisés pour prédiction énergétique:
        - max_depth: 6 (compromis complexité/généralisation)
        - learning_rate: 0.1 (apprentissage équilibré)
        - n_estimators: 200 (boosting iterations)
        - early_stopping_rounds: 20 (régularisation)
        
        Args:
            train_df: Dataset d'entraînement
            val_df: Dataset de validation
            hyperparams: Dict de paramètres custom
        
        Returns:
            Dict des résultats d'entraînement
        """
        logger.info("\n" + "="*80)
        logger.info("ENTRAÎNEMENT DU MODÈLE XGBOOST")
        logger.info("="*80)
        
        # Paramètres par défaut
        if hyperparams is None:
            hyperparams = {
                'objective': 'reg:squarederror',
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'gamma': 1,
                'min_child_weight': 5,
                'random_state': 42,
                'n_jobs': -1
            }
        
        logger.info("\nHyperparamètres:")
        for key, val in hyperparams.items():
            logger.info(f"  {key}: {val}")
        
        # Préparer les données
        X_train, y_train, feature_names = self.prepare_features(train_df)
        # Stocker les feature names pour utilisation dans predict()
        self.feature_names = feature_names
        # Utiliser les mêmes features pour validation
        X_val, y_val, _ = self.prepare_features(val_df, feature_names=feature_names)
        
        # Initialiser et entraîner
        self.model = xgb.XGBRegressor(
            n_estimators=200,
            early_stopping_rounds=20,
            eval_metric='rmse',
            **hyperparams
        )
        
        logger.info("\nDémarrage de l'entraînement...")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=True
        )
        
        # Performances
        y_train_pred = self.model.predict(X_train)
        y_val_pred = self.model.predict(X_val)
        
        train_mae = mean_absolute_error(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        train_r2 = r2_score(y_train, y_train_pred)
        
        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        val_r2 = r2_score(y_val, y_val_pred)
        
        logger.info(f"\nRésultats d'entraînement:")
        logger.info(f"  TRAIN - MAE: {train_mae:.1f} MW, RMSE: {train_rmse:.1f} MW, R²: {train_r2:.3f}")
        logger.info(f"  VAL   - MAE: {val_mae:.1f} MW, RMSE: {val_rmse:.1f} MW, R²: {val_r2:.3f}")
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\nTop 10 Features importantes:")
        for idx, row in self.feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']:40s}: {row['importance']:.4f}")
        
        return {
            'train_mae': train_mae,
            'train_rmse': train_rmse,
            'train_r2': train_r2,
            'val_mae': val_mae,
            'val_rmse': val_rmse,
            'val_r2': val_r2,
            'n_estimators_used': self.model.best_iteration + 1 if hasattr(self.model, 'best_iteration') else 200
        }
    
    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fait les prédictions sur l'ensemble de test.
        
        Args:
            test_df: Dataset de test
        
        Returns:
            DataFrame avec dates, vraies valeurs, et prédictions
        """
        logger.info("\n" + "="*80)
        logger.info("PRÉDICTIONS SUR LE TEST SET")
        logger.info("="*80)
        
        # Préparer les données
        X_test, y_test, _ = self.prepare_features(test_df, feature_names=self.feature_names)
        
        # Prédictions
        y_pred = self.model.predict(X_test)
        
        # Métriques
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        logger.info(f"\nRésultats sur TEST set:")
        logger.info(f"  MAE: {mae:.1f} MW")
        logger.info(f"  RMSE: {rmse:.1f} MW")
        logger.info(f"  R²: {r2:.3f}")
        logger.info(f"  MAPE: {mape:.1f}%")
        
        # Résultats
        results_df = test_df[[self.date_col, self.target_col]].copy()
        results_df.columns = ['date', 'consommation_reelle']
        results_df['consommation_predite'] = y_pred
        results_df['erreur_absolue'] = np.abs(y_test - y_pred)
        results_df['erreur_pct'] = (np.abs(y_test - y_pred) / y_test) * 100
        
        self.predictions = results_df
        
        return results_df
    
    def save_model(self, output_path: Path) -> None:
        """Sauvegarde le modèle."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_file = output_path / "xgboost_model.json"
        self.model.save_model(model_file)
        logger.info(f"Modèle sauvegardé: {model_file}")


def run_complete_modeling_pipeline(df_features: pd.DataFrame,
                                   output_path: Path = Path("data")) -> Tuple[pd.DataFrame, Dict]:
    """
    Lance le pipeline complet de modélisation.
    
    Args:
        df_features: Dataset avec features
        output_path: Chemin de sortie
    
    Returns:
        Tuple (predictions_df, results_dict)
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialiser le pipeline
    pipeline = TemporalModelingPipeline(df_features)
    
    # Séparation temporelle
    train_df, val_df, test_df = pipeline.temporal_train_test_split()
    
    # Entraînement
    train_results = pipeline.train_model(train_df, val_df)
    
    # Prédictions
    predictions_df = pipeline.predict(test_df)
    
    # Sauvegarder
    output_file = output_path / "predictions.csv"
    predictions_df.to_csv(output_file, index=False)
    logger.info(f"Prédictions sauvegardées: {output_file}")
    
    # Modèle
    pipeline.save_model(output_path)
    
    # Feature importance
    importance_file = output_path / "feature_importance.csv"
    pipeline.feature_importance.to_csv(importance_file, index=False)
    logger.info(f"Feature importance sauvegardée: {importance_file}")
    
    return predictions_df, train_results


if __name__ == "__main__":
    """Exemple d'utilisation."""
    from scripts.feature_engineering import create_feature_dataset
    from scripts.data_pipeline import EnergyDataPipeline
    
    # Charger données
    pipeline_data = EnergyDataPipeline(
        Path("data/Data_Climat"),
        Path("data/Data_eCO2"),
        Path("output")
    )
    df_merged = pipeline_data.run(save_intermediate=False)
    
    # Features
    df_features = create_feature_dataset(df_merged)
    
    # Modélisation
    predictions, results = run_complete_modeling_pipeline(df_features)
    
    print("\nPrédictions:")
    print(predictions.head())
    print(f"\nRésultats d'entraînement: {results}")
