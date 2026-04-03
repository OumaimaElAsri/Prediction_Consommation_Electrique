from __future__ import annotations

from pathlib import Path
from typing import Iterable
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


class EnergyDataPipeline:
    """Load, clean and merge weather and RTE datasets."""

    def __init__(self, meteo_path: Path, rte_path: Path, output_path: Path) -> None:
        self.meteo_path = Path(meteo_path)
        self.rte_path = Path(rte_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def run(self, save_intermediate: bool = True) -> pd.DataFrame:
        df_meteo = self._load_meteo_data()
        df_rte = self._load_rte_data()
        df_merged = self._merge_and_clean(df_meteo, df_rte)

        if save_intermediate:
            self._save_intermediate(df_meteo, "01_meteo_raw.csv")
            self._save_intermediate(df_rte, "02_rte_raw.csv")
            self._save_intermediate(df_merged, "03_merged_raw.csv")
            self._save_intermediate(df_merged, "04_data_final.csv")

        return df_merged

    def _load_meteo_data(self) -> pd.DataFrame:
        csv_files = sorted(self.meteo_path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"Aucun fichier meteo trouve dans {self.meteo_path}")

        frames = []
        for file_path in csv_files:
            df = pd.read_csv(file_path)
            if "date" not in df.columns:
                continue
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            dept_code = self._extract_department_code(file_path.name)
            if dept_code is not None:
                df["code_dept"] = dept_code
            frames.append(df)

        if not frames:
            raise ValueError("Aucun fichier meteo valide avec une colonne 'date'")

        meteo = pd.concat(frames, ignore_index=True)
        meteo = meteo.sort_values("date").drop_duplicates(subset=["date", "code_dept"], keep="last")

        numeric_cols = [c for c in meteo.select_dtypes(include="number").columns if c != "code_dept"]
        aggregated = meteo.groupby("date", as_index=False)[numeric_cols].mean()
        return aggregated

    def _load_rte_data(self) -> pd.DataFrame:
        candidates = list(self._iter_rte_files())
        if not candidates:
            raise FileNotFoundError(f"Aucun fichier RTE trouve dans {self.rte_path}")

        frames = []
        for file_path in candidates:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            else:
                try:
                    df = pd.read_excel(file_path)
                except Exception:
                    # Some legacy RTE files are text files with xls extension.
                    try:
                        df = pd.read_csv(file_path, sep="\t")
                    except Exception:
                        df = pd.read_csv(file_path)
            if "date" not in df.columns:
                continue
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            frames.append(df)

        if not frames:
            raise ValueError("Aucun fichier RTE valide avec une colonne 'date'")

        rte = pd.concat(frames, ignore_index=True)
        rte = rte.sort_values("date").drop_duplicates(subset=["date"], keep="last")
        return rte

    def _merge_and_clean(self, meteo: pd.DataFrame, rte: pd.DataFrame) -> pd.DataFrame:
        df = pd.merge(rte, meteo, on="date", how="inner")
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")

        numeric_cols = df.select_dtypes(include="number").columns
        if len(numeric_cols) > 0:
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear", limit_direction="both")

        return df.reset_index(drop=True)

    def _save_intermediate(self, df: pd.DataFrame, filename: str) -> None:
        output_file = self.output_path / filename
        df.to_csv(output_file, index=False)
        logger.info("Saved %s", output_file)

    def _iter_rte_files(self) -> Iterable[Path]:
        patterns = ("*.csv", "*.xlsx", "*.xls")
        for pattern in patterns:
            yield from sorted(self.rte_path.glob(pattern))

    @staticmethod
    def _extract_department_code(filename: str) -> str | None:
        match = re.search(r"H_(\d{2,3})_", filename)
        return match.group(1) if match else None
