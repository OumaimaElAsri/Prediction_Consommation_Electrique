from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    def __init__(self, df: pd.DataFrame, target_col: str = "consommation_mwh") -> None:
        self.df = df.copy()
        self.target_col = target_col
        if "date" not in self.df.columns:
            raise ValueError("La colonne 'date' est obligatoire pour le feature engineering")
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        self.df = self.df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    def build_all_features(self) -> pd.DataFrame:
        df = self.df.copy()
        df = self._add_calendar_features(df)
        df = self._add_lag_features(df)
        df = self._add_rolling_features(df)
        df = self._add_interactions(df)

        lag_cols = [c for c in df.columns if c.startswith(f"{self.target_col}_lag_")]
        if lag_cols:
            df = df.dropna(subset=lag_cols).reset_index(drop=True)

        return df

    def _add_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["hour"] = df["date"].dt.hour
        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["day_of_year"] = df["date"].dt.dayofyear
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.target_col not in df.columns:
            return df
        for lag in (1, 2, 24):
            df[f"{self.target_col}_lag_{lag}"] = df[self.target_col].shift(lag)
        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.target_col not in df.columns:
            return df
        for window in (6, 24):
            df[f"{self.target_col}_rolling_mean_{window}"] = (
                df[self.target_col].rolling(window=window, min_periods=1).mean()
            )
        return df

    def _add_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        if "temperature" in df.columns:
            df["temp_x_weekend"] = df["temperature"] * df.get("is_weekend", 0)
        if {"temperature", "humidite"}.issubset(df.columns):
            df["temp_x_humidite"] = df["temperature"] * df["humidite"]
        return df


def create_feature_dataset(df_merged: pd.DataFrame, output_path: Optional[Path] = None) -> pd.DataFrame:
    features = FeatureEngineer(df_merged).build_all_features()
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    features[numeric_cols] = features[numeric_cols].interpolate(method="linear", limit_direction="both")

    if output_path is not None:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        features.to_csv(output_dir / "features_engineered.csv", index=False)
        logger.info("Saved %s", output_dir / "features_engineered.csv")

    return features