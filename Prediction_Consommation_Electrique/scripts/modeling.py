import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, List
import logging

import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


class TemporalModelingPipeline:
    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str = "consommation_mwh",
        date_col: str = "date",
    ):
        self.df = df.copy()
        self.df[date_col] = pd.to_datetime(self.df[date_col], errors="coerce")
        self.df = self.df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)

        self.target_col = target_col
        self.date_col = date_col
        self.model = None
        self.feature_importance = None
        self.predictions = None
        self.feature_names: List[str] = []

        logger.info("Pipeline modelisation initialise (%s lignes)", len(self.df))
    
    def temporal_train_test_split(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        n_rows = len(self.df)
        if n_rows < 30:
            raise ValueError("Pas assez de donnees pour un split train/validation/test robuste")

        train_end = int(n_rows * 0.70)
        val_end = int(n_rows * 0.85)

        train_df = self.df.iloc[:train_end].copy()
        val_df = self.df.iloc[train_end:val_end].copy()
        test_df = self.df.iloc[val_end:].copy()

        return train_df, val_df, test_df
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        feature_names: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        df = df.copy()
        y = df[self.target_col].values

        if feature_names is None:
            exclude_cols = {self.date_col, self.target_col}
            numeric_df = df.select_dtypes(include=["number"])
            feature_names = [col for col in numeric_df.columns if col not in exclude_cols]

        X = df[feature_names].fillna(df[feature_names].median()).values

        return X, y, feature_names
    
    def train_model(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        hyperparams: Optional[Dict] = None,
    ) -> Dict:
        if hyperparams is None:
            hyperparams = {
                "objective": "reg:squarederror",
                "max_depth": 6,
                "learning_rate": 0.05,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
                "n_jobs": -1,
            }

        X_train, y_train, feature_names = self.prepare_features(train_df)
        self.feature_names = feature_names
        X_val, y_val, _ = self.prepare_features(val_df, feature_names=feature_names)

        self.model = xgb.XGBRegressor(
            n_estimators=200,
            early_stopping_rounds=20,
            eval_metric="rmse",
            **hyperparams,
        )
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        y_train_pred = self.model.predict(X_train)
        y_val_pred = self.model.predict(X_val)

        train_mae = mean_absolute_error(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        train_r2 = r2_score(y_train, y_train_pred)

        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        val_r2 = r2_score(y_val, y_val_pred)

        self.feature_importance = pd.DataFrame({
            "feature": feature_names,
            "importance": self.model.feature_importances_,
        }).sort_values("importance", ascending=False)

        return {
            "train_mae": train_mae,
            "train_rmse": train_rmse,
            "train_r2": train_r2,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "val_r2": val_r2,
            "n_estimators_used": self.model.best_iteration + 1 if hasattr(self.model, "best_iteration") else 200,
        }
    
    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        X_test, y_test, _ = self.prepare_features(test_df, feature_names=self.feature_names)
        y_pred = self.model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        safe_denominator = np.where(y_test == 0, 1, y_test)
        mape = np.mean(np.abs((y_test - y_pred) / safe_denominator)) * 100

        results_df = test_df[[self.date_col, self.target_col]].copy()
        results_df.columns = ["date", "consommation_reelle"]
        results_df["consommation_predite"] = y_pred
        results_df["erreur_absolue"] = np.abs(y_test - y_pred)
        results_df["erreur_pct"] = (np.abs(y_test - y_pred) / safe_denominator) * 100
        results_df["mae_global"] = mae
        results_df["rmse_global"] = rmse
        results_df["r2_global"] = r2
        results_df["mape_global"] = mape

        self.predictions = results_df
        return results_df
    
    def save_model(self, output_path: Path) -> None:
        """Sauvegarde le modèle."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_file = output_path / "xgboost_model.json"
        self.model.save_model(model_file)
        logger.info(f"Modèle sauvegardé: {model_file}")


def run_complete_modeling_pipeline(
    df_features: pd.DataFrame,
    output_path: Path = Path("output"),
) -> Tuple[pd.DataFrame, Dict]:
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    pipeline = TemporalModelingPipeline(df_features)
    train_df, val_df, test_df = pipeline.temporal_train_test_split()
    train_results = pipeline.train_model(train_df, val_df)
    predictions_df = pipeline.predict(test_df)

    output_file = output_path / "predictions.csv"
    predictions_df.to_csv(output_file, index=False)

    importance_file = output_path / "feature_importance.csv"
    pipeline.feature_importance.to_csv(importance_file, index=False)

    return predictions_df, train_results
