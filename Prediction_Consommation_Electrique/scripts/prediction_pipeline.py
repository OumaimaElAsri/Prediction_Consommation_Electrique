import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import logging

from scripts.data_pipeline import EnergyDataPipeline
from scripts.feature_engineering import create_feature_dataset
from scripts.modeling import run_complete_modeling_pipeline

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class PredictionPipeline:
    def __init__(self, meteo_path: Path, rte_path: Path, output_path: Path, data_processed_path: Path = None):
        self.meteo_path = Path(meteo_path)
        self.rte_path = Path(rte_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        if data_processed_path is None:
            self.data_processed_path = Path("data") / "processed_data.csv"
        else:
            self.data_processed_path = Path(data_processed_path)
        logger.info("="*80)
        logger.info("PIPELINE DE PRÉDICTION - INITIALISATION")
        logger.info("="*80)

    def run(self) -> Tuple[pd.DataFrame, Dict]:
        logger.info("\n" + "█"*80)
        logger.info("█ ÉTAPE 1: CHARGEMENT & NETTOYAGE DONNÉES")
        logger.info("█"*80)
        data_pipeline = EnergyDataPipeline(
            meteo_path=self.meteo_path,
            rte_path=self.rte_path,
            output_path=self.output_path
        )
        df_merged = data_pipeline.run(save_intermediate=False)
        logger.info(f"✓ Données nettoyées: {df_merged.shape[0]} lignes × {df_merged.shape[1]} colonnes")

        logger.info("\n" + "█"*80)
        logger.info("█ ÉTAPE 2: FEATURE ENGINEERING")
        logger.info("█"*80)
        df_features = create_feature_dataset(df_merged, self.output_path)
        logger.info(f"✓ Features créées: {df_features.shape[0]} lignes × {df_features.shape[1]} colonnes")
        logger.info(f" Nouvelles colonnes: {df_features.shape[1] - df_merged.shape[1]}")

        logger.info("\n" + "█"*80)
        logger.info("█ ÉTAPE 3: MODÉLISATION & PRÉDICTIONS")
        logger.info("█"*80)
        predictions_df, train_results = run_complete_modeling_pipeline(
            df_features, self.output_path
        )

        logger.info("\n" + "█"*80)
        logger.info("█ ÉTAPE 4: EXPORT DATASET FINAL")
        logger.info("█"*80)
        dataset_final = self._create_final_dataset(df_features, predictions_df)
        self.data_processed_path.parent.mkdir(parents=True, exist_ok=True)
        dataset_final.to_csv(self.data_processed_path, index=False)
        logger.info(f"✓ Dataset final sauvegardé: {self.data_processed_path}")
        logger.info(f" Shape: {dataset_final.shape[0]} lignes × {dataset_final.shape[1]} colonnes")

        logger.info("\n" + "█"*80)
        logger.info("█ RÉSUMÉ FINAL")
        logger.info("█"*80)
        self._print_summary(dataset_final, train_results, predictions_df)
        return dataset_final, train_results

    def _create_final_dataset(self, df_features: pd.DataFrame, predictions_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Création du dataset final...")
        df_final = df_features.merge(
            predictions_df[['date', 'consommation_predite', 'erreur_absolue', 'erreur_pct']],
            on='date',
            how='inner'
        )
        col_order = [
            'date', 'consommation_mwh', 'consommation_predite', 'erreur_absolue', 'erreur_pct'
        ]
        remaining_cols = [col for col in df_final.columns if col not in col_order]
        col_order.extend(remaining_cols)
        df_final = df_final[col_order]
        logger.info(f"Dataset final: {df_final.shape[0]} lignes × {df_final.shape[1]} colonnes")
        return df_final

    def _print_summary(self, dataset_final: pd.DataFrame, train_results: Dict, predictions_df: pd.DataFrame) -> None:
        print("\n" + "="*80)
        print("RÉSUMÉ DES RÉSULTATS")
        print("="*80)
        print("\n📊 DONNÉES")
        print(f" Dataset final: {dataset_final.shape[0]} lignes × {dataset_final.shape[1]} colonnes")
        print(f" Fichier: {self.data_processed_path}")
        print("\n🎯 PERFORMANCE ENTRAÎNEMENT")
        print(f" Train MAE: {train_results['train_mae']:.1f} MW")
        print(f" Train R²: {train_results['train_r2']:.3f}")
        print(f" Val MAE: {train_results['val_mae']:.1f} MW")
        print(f" Val R²: {train_results['val_r2']:.3f}")
        print("\n🔮 PRÉDICTIONS TEST")
        mae_test = predictions_df['erreur_absolue'].mean()
        mape_test = predictions_df['erreur_pct'].mean()
        print(f" Prédictions: {len(predictions_df)} points")
        print(f" MAE: {mae_test:.1f} MW")
        print(f" MAPE: {mape_test:.1f}%")
        print("\n📈 STATISTIQUES FINALES")
        print(f" Consommation moyenne réelle: {dataset_final['consommation_mwh'].mean():.1f} MW")
        print(f" Consommation moyenne prédite: {dataset_final['consommation_predite'].mean():.1f} MW")
        print(f" Erreur moyenne: {dataset_final['erreur_absolue'].mean():.1f} MW")
        print("\n" + "="*80)
        print("✅ PIPELINE COMPLÉTÉ AVEC SUCCÈS")
        print("="*80)


def main():
    pipeline = PredictionPipeline(
        meteo_path=Path("data/Data_Climat"),
        rte_path=Path("data/Data_eCO2"),
        output_path=Path("output"),
        data_processed_path=Path("data") / "processed_data.csv"
    )
    try:
        dataset_final, results = pipeline.run()
        return 0
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)

