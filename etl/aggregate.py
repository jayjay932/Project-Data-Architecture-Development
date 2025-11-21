"""
This module contains functions for aggregating cleaned data from various sources.
It prepares ready-to-use datasets for building API endpoints.
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR_SILVER = ROOT / "data" / "silver_layer"
DIR__GOLD = ROOT / "data" / "gold_layer"


def read_cleaned_csv_files(file_name: str) -> pd.DataFrame:
    """
    Read csv files from silver layer
    Args:
        file_name (str): Name of the cleaned CSV file to read.
    Returns:
        pd.DataFrame: Dataframe containing the cleaned data.
    """
    file_path = DIR_SILVER / file_name
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    df = pd.read_csv(file_path, sep=";", encoding="utf-8", header=0)
    if "code_commune" in df.columns:
        df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
    return df


def save_to_gold(df: pd.DataFrame, filename: str) -> None:
    """
    Save the aggregated dataframe to a CSV file in the gold layer (data/gold_layer/).
    
    Args:
        df (pd.DataFrame): Aggregated dataframe.
        filename (str): Name of the file to save the aggregated CSV file as.
    Returns:
        None.
    """    
    output_path = DIR__GOLD / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, header=True, sep=";", encoding="utf-8")


def agg_all():
    """
    wide table with all columns aggregated by arrondissement, year, type_local and nombre_pieces_principales
    and enriched with median revenu, logement sociaux and air quality data
    """
    # read data from silver layer
    cleaned_dvf_data = read_cleaned_csv_files("cleaned_dvf_data.csv")
    med_revenu_data = read_cleaned_csv_files("cleaned_med_revenu_data.csv")
    logements_sociaux_data = read_cleaned_csv_files("cleaned_logement_sociaux_data.csv")
    air_quality_data = read_cleaned_csv_files("cleaned_air_quality_data.csv")

    # aggregate DVF data by arrondissement, year, type_local
    agg_dvf_data = cleaned_dvf_data.groupby(["code_commune", "annee", "type_local", "nombre_pieces_principales"]
        ).agg(
            prix_m2_median=("prix_m2", "median"),
        ).reset_index()

    # enrich cleaned DVF data with median revenu, logement sociaux and air quality data
    agg_dvf_data_all= agg_dvf_data.merge(
            med_revenu_data, on="code_commune", how="left"
        ).merge(
            logements_sociaux_data, on="code_commune", how="left"
        ).merge(
            air_quality_data, on="code_commune", how="left"
        )
    
    
    save_to_gold(agg_dvf_data_all, "all_data.csv")


def main(): 
    agg_all()


if __name__ == "__main__":
    main()
