from pathlib import Path
from dataclasses import dataclass
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

METEO_DATA_DIR = DATA_DIR / "Data_Climat"
RTE_DATA_DIR = DATA_DIR / "Data_eCO2"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class MeteoConfig:
    data_dir: Path = METEO_DATA_DIR
    file_pattern: str = "*.csv"
    dept_code_pattern: str = r'H_(\d{2,3})_'
    columns_to_keep: Optional[list] = None
    encoding: str = 'utf-8'
    delimiter: str = ','
    date_column: str = 'date'
    date_format: Optional[str] = None
    datetime_columns: list = None
    
    def __post_init__(self):
        if self.datetime_columns is None:
            self.datetime_columns = [self.date_column]


@dataclass
class RTEConfig:
    data_dir: Path = RTE_DATA_DIR
    file_pattern: str = "*.xls*"
    skiprows: int = 3
    sheet_name: Optional[int] = 0
    
    # Colonnes à utiliser (None = toutes les colonnes)
    columns_to_keep: Optional[list] = None
    
    # Nom de la colonne temporelle
    date_column: str = 'date'
    
    # Format de la date (None = inférer automatiquement)
    date_format: Optional[str] = None
    
    # Colonnes à convertir en type datetime
    datetime_columns: list = None
    
    def __post_init__(self):
        if self.datetime_columns is None:
            self.datetime_columns = [self.date_column]


@dataclass
class FusionConfig:
    """Configuration pour la fusion des données."""
    
    # Clé de jointure - colonne temporelle
    meteo_date_column: str = 'date'
    rte_date_column: str = 'date'
    
    # Type de jointure: 'inner', 'outer', 'left', 'right'
    how: str = 'inner'
    
    # Tolérance temporelle en secondes (pour les jointures fuzzy)
    # 0 = jointure exacte
    time_tolerance: int = 0
    
    # Fusionner sur les codes départements (si disponibles)
    merge_on_dept: bool = False


@dataclass
class QualityConfig:
    """Configuration pour le nettoyage et la qualité des données."""
    
    # Méthode d'interpolation pour les données numériques
    numeric_interpolation: str = 'linear'
    
    # Limite d'interpolation (nombre de points max à interpoler)
    interpolation_limit: int = 4
    
    # Méthode de remplissage pour catégories
    categorical_fill: str = 'forward'
    
    # Méthode de détection des outliers: 'iqr', 'zscore', 'isolation_forest'
    outlier_method: str = 'iqr'
    
    # Multiplicateur IQR pour les outliers (défaut: 1.5)
    iqr_multiplier: float = 1.5
    
    # Seuil Z-score pour les outliers
    zscore_threshold: float = 3.0
    
    # Sauvegarder les rapports de qualité
    save_quality_report: bool = True
    
    # Supprimer les doublons complets
    remove_duplicates: bool = True


@dataclass
class PipelineConfig:
    """Configuration globale du pipeline."""
    
    # Configurations spécifiques
    meteo: MeteoConfig = None
    rte: RTEConfig = None
    fusion: FusionConfig = None
    quality: QualityConfig = None
    
    # Chemins
    output_dir: Path = OUTPUT_DIR
    logs_dir: Path = LOGS_DIR
    
    # Niveaux de logging
    log_level: str = 'INFO'
    
    # Sauvegarder les fichiers intermédiaires
    save_intermediate: bool = True
    
    # Format de sortie: 'csv', 'parquet', 'both'
    output_format: str = 'both'
    
    # Compression pour Parquet
    parquet_compression: str = 'snappy'
    
    # Verbose output
    verbose: bool = True
    
    def __post_init__(self):
        if self.meteo is None:
            self.meteo = MeteoConfig()
        if self.rte is None:
            self.rte = RTEConfig()
        if self.fusion is None:
            self.fusion = FusionConfig()
        if self.quality is None:
            self.quality = QualityConfig()


# Configuration par défaut
DEFAULT_CONFIG = PipelineConfig()


# Presets de configuration

class ConfigPresets:
    """Presets de configuration pour différents cas d'usage."""
    
    @staticmethod
    def production() -> PipelineConfig:
        """Configuration pour l'environnement de production."""
        config = PipelineConfig()
        config.log_level = 'WARNING'
        config.save_intermediate = False
        config.verbose = False
        config.quality.save_quality_report = True
        return config
    
    @staticmethod
    def development() -> PipelineConfig:
        """Configuration pour le développement."""
        config = PipelineConfig()
        config.log_level = 'DEBUG'
        config.save_intermediate = True
        config.verbose = True
        return config
    
    @staticmethod
    def testing() -> PipelineConfig:
        """Configuration pour les tests."""
        config = PipelineConfig()
        config.log_level = 'INFO'
        config.save_intermediate = False
        config.output_dir = Path(PROJECT_ROOT) / "test_output"
        config.output_format = 'csv'
        return config


if __name__ == "__main__":
    """Afficher la configuration par défaut."""
    print("=" * 80)
    print("CONFIGURATION PAR DÉFAUT DU PIPELINE")
    print("=" * 80)
    print(f"\nChemin du projet: {PROJECT_ROOT}")
    print(f"Répertoire de sortie: {DEFAULT_CONFIG.output_dir}")
    print(f"Répertoire de logs: {DEFAULT_CONFIG.logs_dir}")
    
    print(f"\n--- Configuration Météo ---")
    print(f"Répertoire: {DEFAULT_CONFIG.meteo.data_dir}")
    print(f"Pattern fichier: {DEFAULT_CONFIG.meteo.file_pattern}")
    print(f"Pattern regex: {DEFAULT_CONFIG.meteo.dept_code_pattern}")
    print(f"Colonne temporelle: {DEFAULT_CONFIG.meteo.date_column}")
    
    print(f"\n--- Configuration RTE ---")
    print(f"Répertoire: {DEFAULT_CONFIG.rte.data_dir}")
    print(f"Lignes à sauter: {DEFAULT_CONFIG.rte.skiprows}")
    print(f"Colonne temporelle: {DEFAULT_CONFIG.rte.date_column}")
    
    print(f"\n--- Configuration Fusion ---")
    print(f"Type de jointure: {DEFAULT_CONFIG.fusion.how}")
    print(f"Colonne temporelle météo: {DEFAULT_CONFIG.fusion.meteo_date_column}")
    print(f"Colonne temporelle RTE: {DEFAULT_CONFIG.fusion.rte_date_column}")
    
    print(f"\n--- Configuration Qualité ---")
    print(f"Interpolation numeric: {DEFAULT_CONFIG.quality.numeric_interpolation}")
    print(f"Remplissage catégorie: {DEFAULT_CONFIG.quality.categorical_fill}")
    print(f"Détection outliers: {DEFAULT_CONFIG.quality.outlier_method}")
    
    print(f"\n--- Configuration Générale ---")
    print(f"Niveau de log: {DEFAULT_CONFIG.log_level}")
    print(f"Sauvegarder intermédiaires: {DEFAULT_CONFIG.save_intermediate}")
    print(f"Format de sortie: {DEFAULT_CONFIG.output_format}")
    print(f"Verbose: {DEFAULT_CONFIG.verbose}")
