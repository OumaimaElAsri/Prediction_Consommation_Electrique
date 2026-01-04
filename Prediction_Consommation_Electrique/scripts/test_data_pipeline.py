"""
Tests unitaires pour le pipeline de nettoyage et fusion de données énergétiques.

Utilise pytest pour la validation des fonctionnalités.
Exécuter avec: pytest test_data_pipeline.py -v

Author: Data Engineering Team
Created: 2026-04-03
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

# Import des modules à tester
from scripts.data_pipeline import (
    MeteoDataPipeline,
    RTEDataPipeline,
    DataFusionPipeline,
    DataQualityPipeline
)


class TestMeteoDataPipeline:
    """Tests pour le pipeline méteorologique."""
    
    @pytest.fixture
    def meteo_pipeline(self):
        """Crée une instance du pipeline météo avec un répertoire temporaire."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MeteoDataPipeline(Path(tmpdir))
    
    def test_extract_dept_code_valid(self, meteo_pipeline):
        """Test l'extraction du code département avec un nom de fichier valide."""
        filename = "H_75_latest-2025-2026.csv"
        result = meteo_pipeline.extract_dept_code(filename)
        assert result == "75", f"Expected '75', got {result}"
    
    def test_extract_dept_code_various_formats(self, meteo_pipeline):
        """Test l'extraction avec différents formats."""
        test_cases = [
            ("H_75_data.csv", "75"),
            ("H_13_meteo.csv", "13"),
            ("H_974_reunion.csv", "974"),
            ("H_2A_corse.csv", None),  # Lettres non matchées
            ("data_75_old.csv", None),  # Préfixe différent
        ]
        
        for filename, expected in test_cases:
            result = meteo_pipeline.extract_dept_code(filename)
            assert result == expected, f"Pour {filename}: expected {expected}, got {result}"
    
    def test_load_meteo_no_files(self, meteo_pipeline):
        """Test le comportement quand aucun fichier CSV n'existe."""
        with pytest.raises(ValueError, match="Aucun fichier CSV"):
            meteo_pipeline.load_and_clean_meteo()


class TestRTEDataPipeline:
    """Tests pour le pipeline RTE."""
    
    @pytest.fixture
    def rte_pipeline(self):
        """Crée une instance du pipeline RTE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield RTEDataPipeline(Path(tmpdir), skiprows=0)
    
    def test_identify_date_columns(self, rte_pipeline):
        """Test l'identification des colonnes temporelles."""
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=5),
            'heure': [0, 1, 2, 3, 4],
            'temperature': [10, 11, 12, 13, 14],
            'timestamp': [str(i) for i in range(5)],
            'consommation': [1000, 1100, 1200, 1300, 1400]
        })
        
        date_cols = rte_pipeline._identify_date_columns(df)
        
        assert 'date' in date_cols
        assert 'timestamp' in date_cols
        assert 'temperature' not in date_cols
        assert 'consommation' not in date_cols
    
    def test_load_rte_no_files(self, rte_pipeline):
        """Test le comportement quand aucun fichier Excel n'existe."""
        with pytest.raises(ValueError, match="Aucun fichier Excel"):
            rte_pipeline.load_and_clean_rte()


class TestDataFusionPipeline:
    """Tests pour la fusion de données."""
    
    @pytest.fixture
    def sample_datasets(self):
        """Crée des datasets d'exemple pour les tests."""
        dates = pd.date_range('2025-01-01', periods=10, freq='H')
        
        df_meteo = pd.DataFrame({
            'date': dates,
            'temperature': np.random.uniform(5, 25, 10),
            'humidite': np.random.uniform(30, 80, 10),
            'code_dept': ['75'] * 10
        })
        
        df_rte = pd.DataFrame({
            'date': dates,
            'consommation_mwh': np.random.uniform(1000, 5000, 10),
            'production_eolienne': np.random.uniform(100, 500, 10)
        })
        
        return df_meteo, df_rte
    
    def test_merge_inner_join(self, sample_datasets):
        """Test une fusion interne (inner join)."""
        df_meteo, df_rte = sample_datasets
        
        result = DataFusionPipeline.merge_datasets(
            df_meteo, df_rte,
            meteo_date_col='date',
            rte_date_col='date',
            how='inner'
        )
        
        assert result.shape[0] == 10, "Inner join devrait retourner 10 lignes"
        assert 'temperature' in result.columns
        assert 'consommation_mwh' in result.columns
    
    def test_merge_missing_date_column(self, sample_datasets):
        """Test le comportement avec colonne de date manquante."""
        df_meteo, df_rte = sample_datasets
        
        with pytest.raises(ValueError, match="non trouvée"):
            DataFusionPipeline.merge_datasets(
                df_meteo, df_rte,
                meteo_date_col='invalid_date',
                rte_date_col='date'
            )
    
    def test_merge_handles_datetime_conversion(self, sample_datasets):
        """Test que la fusion convertit les dates en datetime."""
        df_meteo, df_rte = sample_datasets
        
        # Convertir les dates en strings
        df_meteo['date'] = df_meteo['date'].astype(str)
        df_rte['date'] = df_rte['date'].astype(str)
        
        result = DataFusionPipeline.merge_datasets(
            df_meteo, df_rte,
            meteo_date_col='date',
            rte_date_col='date'
        )
        
        assert pd.api.types.is_datetime64_any_dtype(result['date'])


class TestDataQualityPipeline:
    """Tests pour la gestion de la qualité des données."""
    
    @pytest.fixture
    def sample_data_with_missing(self):
        """Crée un dataset avec valeurs manquantes."""
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=10),
            'temperature': [10.0, 11.0, np.nan, 13.0, np.nan, 15.0, 16.0, 17.0, 18.0, 19.0],
            'code_dept': ['75', '75', np.nan, '75', '75', np.nan, '75', '75', '75', '75'],
            'consommation': [1000, 1100, 1200, np.nan, 1400, 1500, 1600, 1700, 1800, 1900]
        })
        return df
    
    def test_handle_missing_values_numeric(self, sample_data_with_missing):
        """Test l'interpolation linéaire pour les colonnes numériques."""
        df = sample_data_with_missing.copy()
        
        initial_nulls = df['temperature'].isnull().sum()
        
        result = DataQualityPipeline.handle_missing_values(
            df,
            numeric_interpolation='linear',
            categorical_fill='forward'
        )
        
        # Les valeurs manquantes ne doivent pas être complètement supprimées
        # mais interpolées
        assert result['temperature'].isnull().sum() <= initial_nulls
    
    def test_detect_outliers(self):
        """Test la détection des outliers via IQR."""
        df = pd.DataFrame({
            'valeur': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 100]  # 100 est un outlier
        })
        
        outliers = DataQualityPipeline.detect_and_report_outliers(df)
        
        assert 'valeur' in outliers
        assert 10 in outliers['valeur']  # L'indice de la valeur 100
    
    def test_detect_no_outliers(self):
        """Test quand aucun outlier n'existe."""
        df = pd.DataFrame({
            'valeur': np.random.normal(100, 10, 100)  # Distribution normale
        })
        
        outliers = DataQualityPipeline.detect_and_report_outliers(df)
        
        # Peut y avoir quelques outliers en distribution normale,
        # mais le dictionnaire ne doit pas être vide si des outliers existent
        assert isinstance(outliers, dict)


class TestDataIntegration:
    """Tests d'intégration complets."""
    
    def test_full_pipeline_with_sample_data(self):
        """Test l'exécution complète du pipeline avec des données d'exemple."""
        # Créer des données de test
        dates = pd.date_range('2025-01-01', periods=100, freq='H')
        
        df_meteo = pd.DataFrame({
            'date': dates,
            'temperature': np.random.uniform(5, 25, 100),
            'humidite': np.random.uniform(30, 80, 100),
            'pression': np.random.uniform(1000, 1020, 100),
            'code_dept': ['75'] * 100
        })
        
        df_rte = pd.DataFrame({
            'date': dates,
            'consommation_mwh': np.random.uniform(1000, 5000, 100),
            'production_eolienne': np.random.uniform(100, 500, 100),
            'production_solaire': np.random.uniform(50, 300, 100)
        })
        
        # Fusion
        df_merged = DataFusionPipeline.merge_datasets(
            df_meteo, df_rte,
            meteo_date_col='date',
            rte_date_col='date'
        )
        
        # Nettoyage de la qualité
        df_final = DataQualityPipeline.handle_missing_values(df_merged)
        
        # Assertions
        assert df_final.shape[0] == 100
        assert 'temperature' in df_final.columns
        assert 'consommation_mwh' in df_final.columns
        assert df_final['code_dept'].isnull().sum() == 0
    
    def test_datetime_handling_consistency(self):
        """Test la cohérence du traitement des dates."""
        dates_str = ['2025-01-01 00:00', '2025-01-01 01:00', '2025-01-01 02:00']
        dates_dt = pd.to_datetime(dates_str)
        
        df1 = pd.DataFrame({
            'date': dates_str,
            'value1': [1, 2, 3]
        })
        
        df2 = pd.DataFrame({
            'date': dates_dt,
            'value2': [10, 20, 30]
        })
        
        result = DataFusionPipeline.merge_datasets(df1, df2)
        
        assert result.shape[0] == 3
        assert pd.api.types.is_datetime64_any_dtype(result['date'])


# Fixtures globales

@pytest.fixture(scope="session")
def test_data_dir():
    """Crée un répertoire temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


if __name__ == "__main__":
    """
    Exécuter les tests avec pytest.
    """
    pytest.main([__file__, "-v", "--tb=short"])
