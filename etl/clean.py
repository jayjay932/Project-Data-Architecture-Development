"""
This module contains functions for cleaning data from various sources.

Data sources include CSV files (data/bronze_layer/*.csv): 
* DVF - Demandes de valeurs foncières 2020-2025 (data.gouv.fr) containing real estate transaction data in France.
* Air quality data - Air quality measurements in Paris, France (airparif.fr) 
* Public transport data - RATP open data (data.ratp.fr) containing information about public transport in Paris, France.
"""

import pandas as pd
import numpy as np
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIR_BRONZE = ROOT / "data" / "bronze_layer"
DIR_SILVER = ROOT / "data" / "silver_layer"

def read_dvf_data() -> pd.DataFrame:
    """
    Read DVF data from CSV files for the years 2020 to 2025 and concatenate them into a single dataframe.
    Args:
        None.
    Returns:
        pd.DataFrame: Concatenated DVF dataframe for the years 2020 to 2025.
    """
    df_list = []
    for year in range(2020, 2026):
        file_path = ROOT / "data" / "bronze_layer" / f"dvf_75_{year}.csv"
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        df = pd.read_csv(file_path, sep=",", encoding="utf-8", header=0)
        df["annee"] = year
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)


def clean_dvf_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess raw DVF data by selecting relevant columns and filtering rows based on specific criteria.
    Args:
        df (pd.DataFrame): Raw DVF dataframe.
    Returns:
        pd.DataFrame: Cleaned DVF dataframe.
    """

    # columns to keep
    columns_to_keep = [
        "id_mutation",
        "code_commune",
        "annee",
        "valeur_fonciere",
        "type_local",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "prix_m2"
    ]

    # filter nature_mutation to keep only sales : "Vente" 
    df = df[df["nature_mutation"] == "Vente"]

    # drop duplicates
    df = df.drop_duplicates()

    # drop rows with missing code_commune, valeur_fonciere, type_local, surface_reelle_bati
    df = df.dropna(subset=["code_commune", "valeur_fonciere", "type_local", "surface_reelle_bati"])

    # filter type_local to keep only "Appartement" and "Maison"
    df = df[df["type_local"].isin(["Appartement", "Maison"])]

    # drop rows with missing or zero values in "valeur_fonciere" or "surface_reelle_bati"
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])

    # exclude "Maison" with surface <10 m2 or > 300 m2 , and "Appartement" with surface > 200 m2
    df = df[~((df["type_local"] == "Maison") & (df["surface_reelle_bati"] < 10))]
    df = df[~((df["type_local"] == "Maison") & (df["surface_reelle_bati"] > 300))]
    df = df[~((df["type_local"] == "Appartement") & (df["surface_reelle_bati"] > 200))]

    # exclude housing with more than 8 principle rooms
    df = df[~(df["nombre_pieces_principales"] > 8)]

    # exclude housing with value valeur_fonciere <= 2€
    df = df[~(df["valeur_fonciere"] <= 2)]

    # calculate price per square meter
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    # keep only relevant columns
    df = df[columns_to_keep]

    # format code_commune as zero-padded 5-digit string
    df["code_commune"] = (df["code_commune"].astype(str).str.zfill(5))

    return df


def load_revenu() -> pd.DataFrame:
    """Load and aggregate the median revenue data at commune level."""
    try:
        path = DIR_BRONZE / "BASE_TD_FILO_DEC_IRIS_2018.xlsx"
        med_revenu = pd.read_excel(path, sheet_name="IRIS_DEC", header=5)
    except ImportError as exc:
        raise ImportError("Install 'openpyxl' to read Excel files with pandas.") from exc
    med_revenu = med_revenu.copy()
    med_revenu["code_commune"] = med_revenu["COM"].astype(str).str.zfill(5)
    med_revenu = med_revenu.rename(columns={"DEC_MED18": "revenu_median"})

    # Several IRIS share the same commune code; aggregate to a single row per commune.
    med_revenu = (
        med_revenu[["code_commune", "revenu_median"]]
        .groupby("code_commune", as_index=False)
        .median()
    )
    return med_revenu


def load_logement_sociaux() -> pd.DataFrame:
    """Load the logement sociaux data for each code_insee"""
    path = DIR_BRONZE / "logements-sociaux-dans-les-communes_IDF.csv"
    logement_sociaux = pd.read_csv(path, sep=";", encoding="latin-1", header=0)
    logement_sociaux = logement_sociaux.copy()
    logement_sociaux["code_commune"] = logement_sociaux["Code Commune"].astype(str).str.zfill(5)
    logement_sociaux["tx_logement_sociaux"] = logement_sociaux["Taux de logements sociaux (%)"].astype(float)
    return logement_sociaux[["code_commune", "tx_logement_sociaux"]]


def load_air_quality() -> pd.DataFrame:
    """
    Load air quality data for Paris, keep the most recent record per area,
    classify pollutant levels using defined thresholds, and compute a global
    air-quality score (worst category among NO2, O3, PM10).
    """
    path = DIR_BRONZE / "air_quality_paris.csv"
    air_quality = pd.read_csv(path, sep=",", encoding="utf-8", header=0)

    # rename ninsee column to code_commune
    air_quality = air_quality.rename(columns={"ninsee": "code_commune"})

    # filter paris areas by keeping INSEE codes starting with '75'
    air_quality["code_commune"] = air_quality["code_commune"].astype(str).str.zfill(5)
    air_quality = air_quality[air_quality["code_commune"].str.startswith("75")]

    # keep the most recent record per INSEE code
    air_quality["date"] = pd.to_datetime(air_quality["date"], format="%d/%m/%Y")
    air_quality = (
        air_quality.sort_values(by="date", ascending=False)
                   .drop_duplicates(subset=["code_commune"], keep="first")
    )

    # air quality classification per polluant
    categories = [
        "Bon",
        "Moyen",
        "Dégradé",
        "Mauvais",
        "Très Mauvais",
        "Extrêmement Mauvais",
    ]

    # NO2 thresholds: 0–40 / 40–90 / 90–120 / 120–230 / 230–340 / >340
    air_quality["qual_no2"] = pd.cut(
        air_quality["no2"],
        bins=[-1, 40, 90, 120, 230, 340, np.inf],
        labels=categories
    )

    # O3 thresholds: 0–50 / 50–100 / 100–130 / 130–240 / 240–380 / >380
    air_quality["qual_o3"] = pd.cut(
        air_quality["o3"],
        bins=[-1, 50, 100, 130, 240, 380, np.inf],
        labels=categories
    )

    # PM10 thresholds: 0–20 / 20–40 / 40–50 / 50–100 / 100–150 / >150
    air_quality["qual_pm10"] = pd.cut(
        air_quality["pm10"],
        bins=[-1, 20, 40, 50, 100, 150, np.inf],
        labels=categories
    )

    # global quality score (worst polluant)
    severity_rank = {
        "Bon": 0,
        "Moyen": 1,
        "Dégradé": 2,
        "Mauvais": 3,
        "Très Mauvais": 4,
        "Extrêmement Mauvais": 5,
    }
    reverse_rank = {v: k for k, v in severity_rank.items()}

    pollutant_cols = ["qual_no2", "qual_o3", "qual_pm10"]

    # Convert qualitative labels to numeric severity levels
    numeric_scores = air_quality[pollutant_cols].replace(severity_rank)

    # Global = worst (maximum) score across pollutants
    max_scores = numeric_scores.max(axis=1)

    # Convert back to qualitative labels
    air_quality["air_quality_global"] = max_scores.replace(reverse_rank)

    # delete date column
    air_quality = air_quality.drop(columns=["date"])

    return air_quality


def save_to_silver(df: pd.DataFrame, filename: str) -> None:
    """
    Save cleaned dataframes to CSV files in the silver layer (data/silver_layer/).
    
    Args:
        df (pd.DataFrame): Cleaned dataframe.
        filename (str): Name of the file to save the cleaned dataframe as.
    Returns:
        None.
    """    
    output_path = DIR_SILVER / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, header=True, sep=";", encoding="utf-8")


def main(): 

    # DVF data
    dvf_data = read_dvf_data()
    cleaned_dvf_data = clean_dvf_data(dvf_data)
    save_to_silver(cleaned_dvf_data, "cleaned_dvf_data.csv")

    # median revenu data
    med_revenu_data = load_revenu()
    save_to_silver(med_revenu_data, "cleaned_med_revenu_data.csv")

    # logement sociaux data
    logements_sociaux_data = load_logement_sociaux()
    save_to_silver(logements_sociaux_data, "cleaned_logement_sociaux_data.csv")

    # air quality data
    air_quality_data = load_air_quality()
    save_to_silver(air_quality_data, "cleaned_air_quality_data.csv")

    # enriched dataset combining DVF, revenu, logements sociaux and air quality
    all_data = (
        cleaned_dvf_data.merge(med_revenu_data, on="code_commune", how="left")
        .merge(logements_sociaux_data, on="code_commune", how="left")
        .merge(air_quality_data, on="code_commune", how="left")
    )
    all_data["tx_logement_sociaux"] = all_data["tx_logement_sociaux"].fillna(0)
    save_to_silver(all_data, "all_data.csv")


if __name__ == "__main__":
    main()
