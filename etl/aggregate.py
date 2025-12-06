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
    wide table with mesures aggregated by year and arrondissement
    """
    # read data from silver layer
    cleaned_dvf_data = read_cleaned_csv_files("cleaned_dvf_data.csv")
    med_revenu_data = read_cleaned_csv_files("cleaned_med_revenu_data.csv")
    logements_sociaux_data = read_cleaned_csv_files("cleaned_logement_sociaux_data.csv")
    air_quality_data = read_cleaned_csv_files("cleaned_air_quality_data.csv")
    pop_dens_data = read_cleaned_csv_files("pop_dens_data.csv")

    # aggregate DVF data by arrondissement and year
    agg_dvf_data = cleaned_dvf_data.groupby(["code_commune", "annee"]
        ).agg(
            prix_m2_median=("prix_m2", "median"),
        ).reset_index()

    # compute housing typology mix based on nombre_pieces_principales
    def categorize_unit(piece_count):
        try:
            count = int(piece_count)
        except (TypeError, ValueError):
            return "studio_t1"
        if count <= 1:
            return "studio_t1"
        if count == 2:
            return "t2"
        if count == 3:
            return "t3"
        if count == 4:
            return "t4"
        return "t5_plus"

    size_mix = cleaned_dvf_data[
        ["code_commune", "annee", "nombre_pieces_principales"]
    ].copy()
    size_mix["categorie_taille"] = size_mix["nombre_pieces_principales"].apply(categorize_unit)

    typology_counts = (
        size_mix.groupby(["code_commune", "annee", "categorie_taille"]).size().unstack(fill_value=0)
    )

    category_columns = ["studio_t1", "t2", "t3", "t4", "t5_plus"]
    for column in category_columns:
        if column not in typology_counts.columns:
            typology_counts[column] = 0

    rename_map = {
        "studio_t1": "transactions_studio_t1",
        "t2": "transactions_t2",
        "t3": "transactions_t3",
        "t4": "transactions_t4",
        "t5_plus": "transactions_t5_plus",
    }
    typology_counts = typology_counts.reset_index().rename(columns=rename_map)

    transaction_columns = list(rename_map.values())
    typology_counts["transactions_total"] = typology_counts[transaction_columns].sum(axis=1)

    total_series = typology_counts["transactions_total"].replace(0, pd.NA)
    share_values = typology_counts[transaction_columns].div(total_series, axis=0) * 100
    share_values = share_values.round(2)
    share_values.columns = [col.replace("transactions_", "part_") for col in transaction_columns]
    typology_counts = pd.concat([typology_counts, share_values], axis=1)

    agg_dvf_data = agg_dvf_data.merge(typology_counts, on=["code_commune", "annee"], how="left")

    # compute surface segment mix based on surface_reelle_bati (m²)
    def categorize_surface_area(surface_value):
        try:
            surface = float(surface_value)
        except (TypeError, ValueError):
            return None
        if surface < 20:
            return "lt_20"
        if surface < 40:
            return "bt_20_40"
        if surface < 60:
            return "bt_40_60"
        if surface < 80:
            return "bt_60_80"
        if surface < 120:
            return "bt_80_120"
        return "gt_120"

    surface_mix = cleaned_dvf_data[["code_commune", "annee", "surface_reelle_bati"]].copy()
    surface_mix["surface_group"] = surface_mix["surface_reelle_bati"].apply(categorize_surface_area)
    surface_mix = surface_mix.dropna(subset=["surface_group"])
    surface_counts = (
        surface_mix.groupby(["code_commune", "annee", "surface_group"])
        .size()
        .unstack(fill_value=0)
    )

    surface_groups = ["lt_20", "bt_20_40", "bt_40_60", "bt_60_80", "bt_80_120", "gt_120"]
    for group_name in surface_groups:
        if group_name not in surface_counts.columns:
            surface_counts[group_name] = 0

    surface_counts = surface_counts.reset_index()
    surface_rename_map = {
        "lt_20": "transactions_surface_lt_20",
        "bt_20_40": "transactions_surface_bt_20_40",
        "bt_40_60": "transactions_surface_bt_40_60",
        "bt_60_80": "transactions_surface_bt_60_80",
        "bt_80_120": "transactions_surface_bt_80_120",
        "gt_120": "transactions_surface_gt_120",
    }
    surface_counts = surface_counts.rename(columns=surface_rename_map)
    surface_transaction_cols = list(surface_rename_map.values())
    surface_totals = surface_counts[surface_transaction_cols].sum(axis=1).replace(0, pd.NA)
    surface_shares = surface_counts[surface_transaction_cols].div(surface_totals, axis=0) * 100
    surface_shares = surface_shares.round(2)
    surface_shares.columns = [
        col.replace("transactions_surface_", "part_surface_") for col in surface_transaction_cols
    ]
    surface_counts = pd.concat([surface_counts, surface_shares], axis=1)

    agg_dvf_data = agg_dvf_data.merge(surface_counts, on=["code_commune", "annee"], how="left")
    
    # calculate the variation of median price/m2 compared to previous year
    agg_dvf_data = agg_dvf_data.sort_values(by=["code_commune", "annee"])
    agg_dvf_data["prix_m2_median_prev_year"] = agg_dvf_data.groupby("code_commune")["prix_m2_median"].shift(1)
    agg_dvf_data["variation"] = (
        (agg_dvf_data["prix_m2_median"] - agg_dvf_data["prix_m2_median_prev_year"])
        / agg_dvf_data["prix_m2_median_prev_year"]
    ) * 100
    mask_no_previous = agg_dvf_data["prix_m2_median_prev_year"].isna() | (
        agg_dvf_data["prix_m2_median_prev_year"] == 0
    )
    agg_dvf_data.loc[mask_no_previous, "variation"] = pd.NA
    agg_dvf_data["variation"] = agg_dvf_data["variation"].round(2)

    # fusion with cleaned DVF socio-economic and demographic data
    agg_dvf_data_all= agg_dvf_data.merge(
            med_revenu_data, on="code_commune", how="left"
        ).merge(
            logements_sociaux_data, on="code_commune", how="left"
        ).merge(
            air_quality_data, on="code_commune", how="left"
        ).merge(
            pop_dens_data, on="code_commune", how="left"
        )
    
    save_to_gold(agg_dvf_data_all, "all_data.csv")


def price_year():
    """
    Median price per square meter by year
    """
    # read data from silver layer
    cleaned_dvf_data = read_cleaned_csv_files("cleaned_dvf_data.csv")

    # aggregate median price/m2 by year
    agg_dvf_data_year = cleaned_dvf_data.groupby(["annee"]).agg(prix_m2_median=("prix_m2", "median"),).reset_index()
    
    save_to_gold(agg_dvf_data_year, "price_year.csv")


def main(): 
    price_year()
    agg_all()

    
if __name__ == "__main__":
    main()
