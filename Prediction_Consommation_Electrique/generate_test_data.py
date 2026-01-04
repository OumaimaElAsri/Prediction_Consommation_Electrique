"""
Script de test avec données simulées.

Crée des données de test pour valider le pipeline sans vraies données.

Utilisation:
    python generate_test_data.py  # Génère les données
    python main.py                 # Exécute le pipeline
    ls output/                     # Affiche les résultats

Author: Data Engineering Team
Created: 2026-04-03
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def generate_meteo_data(
    output_dir: Path,
    n_departments: int = 5,
    days: int = 30,
    seed: int = 42
) -> Path:
    """
    Génère des données météorologiques de test.
    
    Crée n_departments fichiers CSV avec données horaires.
    
    Args:
        output_dir: Répertoire de sortie
        n_departments: Nombre de départements à générer
        days: Nombre de jours de données
        seed: Seed pour reproductibilité
    
    Returns:
        Chemin du répertoire créé
    """
    np.random.seed(seed)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Codes départements de test
    dept_codes = ['75', '13', '69', '75003', '974'][:n_departments]
    
    for dept_code in dept_codes:
        # Générer dates horaires
        start_date = datetime(2025, 1, 1)
        hours = days * 24
        dates = [start_date + timedelta(hours=i) for i in range(hours)]
        
        # Données météo réalistes
        temperatures = 15 + 8 * np.sin(np.arange(hours) * 2 * np.pi / 24) + np.random.normal(0, 2, hours)
        humidity = 60 + 20 * np.sin(np.arange(hours) * 2 * np.pi / 24 + 1) + np.random.normal(0, 5, hours)
        pressure = 1013 + np.random.normal(0, 2, hours)
        wind_speed = 5 + np.abs(np.random.normal(0, 2, hours))
        
        df = pd.DataFrame({
            'date': dates,
            'temperature': temperatures,
            'humidite': np.clip(humidity, 0, 100),
            'pression': pressure,
            'vitesse_vent': wind_speed,
            'precipitation': np.abs(np.random.normal(0, 2, hours))
        })
        
        # Sauvegarder
        filename = output_dir / f"H_{dept_code}_latest-2025-2026.csv"
        df.to_csv(filename, index=False)
        print(f"✓ Données météo générées: {filename.name} ({hours} lignes)")
    
    return output_dir


def generate_rte_data(
    output_dir: Path,
    days: int = 30,
    seed: int = 42
) -> Path:
    """
    Génère des données RTE de test.
    
    Crée un fichier Excel avec données de consommation et production.
    
    Args:
        output_dir: Répertoire de sortie
        days: Nombre de jours de données
        seed: Seed pour reproductibilité
    
    Returns:
        Chemin du répertoire créé
    """
    np.random.seed(seed)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer dates
    start_date = datetime(2025, 1, 1)
    hours = days * 24
    dates = [start_date + timedelta(hours=i) for i in range(hours)]
    
    # Données RTE réalistes (en MW)
    # Consommation avec pattern jour/nuit
    base_consumption = 35000
    consumption = base_consumption + 8000 * np.sin(np.arange(hours) * 2 * np.pi / 24) + np.random.normal(0, 1000, hours)
    
    # Production éolienne aléatoire
    wind_production = 3000 + np.random.gamma(2, 1000, hours)
    
    # Production solaire (0 la nuit)
    solar_production = np.maximum(0, 1000 * np.sin(np.arange(hours) * 2 * np.pi / 24) + np.random.normal(0, 200, hours))
    
    # CO2 based on energy mix
    co2_intensity = 100 + (wind_production + solar_production) * (-0.01) + np.random.normal(0, 10, hours)
    
    df = pd.DataFrame({
        'date': dates,
        'consommation_mwh': consumption,
        'production_eolienne_mwh': wind_production,
        'production_solaire_mwh': solar_production,
        'production_nucleaire_mwh': 40000 + np.random.normal(0, 500, hours),
        'production_hydro_mwh': 5000 + np.random.normal(0, 1000, hours),
        'co2_g_kwh': np.clip(co2_intensity, 0, 500)
    })
    
    # Sauvegarder en "Excel-like" (CSV pour simplicité)
    # En production, utiliser openpyxl pour vrai Excel
    filename = output_dir / "eCO2mix_RTE_tempo_2025-2026.csv"
    df.to_csv(filename, index=False)
    print(f"✓ Données RTE générées: {filename.name} ({hours} lignes)")
    
    # Note: Pour Excel vrai, décommenter:
    # df.to_excel(output_dir / "eCO2mix_RTE_tempo_2025-2026.xlsx", index=False)
    
    return output_dir


def setup_test_environment(
    project_root: Path = Path(".")
) -> dict:
    """
    Configure l'environnement de test complet.
    
    Args:
        project_root: Racine du projet
    
    Returns:
        Dict avec chemins créés
    """
    project_root = Path(project_root)
    
    data_dir = project_root / "data"
    meteo_dir = data_dir / "Data_Climat"
    rte_dir = data_dir / "Data_eCO2"
    output_dir = project_root / "output"
    
    print("🔧 Configuration de l'environnement de test...")
    print(f"   Racine du projet: {project_root}")
    
    # Générer données
    print("\n📊 Génération des données de test...")
    generate_meteo_data(meteo_dir, n_departments=3, days=30)
    generate_rte_data(rte_dir, days=30)
    
    # Créer répertoire output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n✅ Environnement de test prêt!")
    
    return {
        'meteo_dir': meteo_dir,
        'rte_dir': rte_dir,
        'output_dir': output_dir,
        'data_dir': data_dir
    }


if __name__ == "__main__":
    """
    Générer les données de test.
    """
    import sys
    
    project_root = Path(__file__).parent
    
    print("=" * 80)
    print("GÉNÉRATION DE DONNÉES DE TEST")
    print("=" * 80)
    
    paths = setup_test_environment(project_root)
    
    print("\n" + "=" * 80)
    print("PROCHAINES ÉTAPES:")
    print("=" * 80)
    print("\n1. Exécuter le pipeline:")
    print("   python main.py")
    print("\n2. Vérifier les résultats:")
    print(f"   ls {paths['output_dir']}")
    print("\n3. Ou exécuter dans un notebook:")
    print("   jupyter notebook notebooks/02_Pipeline_Complete_Meteo_RTE.ipynb")
    
    print("\n✨ Données de test prêtes!")
