from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POPULATION_PATH = PROJECT_ROOT / "data" / "bronze" / "recensement_pop_paris_insee_2022.xlsx"
SURFACE_PATH = PROJECT_ROOT / "data" / "bronze" / "arrondissements_paris.csv"
REVENUE_PATH = PROJECT_ROOT / "data" / "bronze" / "BASE_TD_FILO_DEC_IRIS_2018.xlsx"
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "demographie_paris.csv"


def load_population(path: Path) -> pd.DataFrame:
    """Load the Paris population data and add column INSEE code."""
    try:
        population = pd.read_excel(path)
    except ImportError as exc:
        raise ImportError("Install 'openpyxl' to read Excel files with pandas.") from exc

    population = population.copy()
    population["code_insee"] = population["code_commune"].astype(int).apply(lambda x: f"75{x:03d}")
    return population[["code_insee", "population_totale"]]


def load_surface(path: Path) -> pd.DataFrame:
    """Load arrondissement surface data from CSV and prepare the INSEE code column."""
    surface = pd.read_csv(path, sep=";", encoding="utf-8")
    surface = surface.copy()
    surface["code_insee"] = surface["Code_INSEE"].astype(str).str.zfill(5)
    return surface[["code_insee", "Surface"]]


def load_revenu(path: Path) -> pd.DataFrame:
    """Load the median revenue data into a dataframe."""
    try:
        med_revenu = pd.read_excel(path, sheet_name="IRIS_DEC", header=5)
    except ImportError as exc:
        raise ImportError("Install 'openpyxl' to read Excel files with pandas.") from exc
    med_revenu = med_revenu.copy()
    med_revenu["code_insee"] = med_revenu["COM"].astype(str).str.zfill(5)
    return med_revenu[["code_insee", "DEC_MED18"]]


def main() -> None:

    # Load datasets
    population = load_population(POPULATION_PATH)
    surface = load_surface(SURFACE_PATH)
    med_revenu = load_revenu(REVENUE_PATH)

    # Merge datasets on INSEE code
    merged_pop_surface = population.merge(surface, on="code_insee", how="left")
    merged = merged_pop_surface.merge(med_revenu, on="code_insee", how="left")

    # Rename columns
    merged.rename(columns={"Surface": "superficie_km2", "DEC_MED18": "revenu_median"}, inplace=True)

    # Calculate population density
    merged["densite_pop_km2"] = merged["population_totale"] / merged["superficie_km2"]

    # Save cleaned data to silver directory
    merged.to_csv(SILVER_PATH, index=False)

if __name__ == "__main__":
    main()
