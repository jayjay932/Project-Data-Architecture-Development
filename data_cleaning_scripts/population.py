"""
Assemble a simple Paris arrondissement population dataset without heavy validation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARRONDISSEMENTS_INPUT = PROJECT_ROOT / "data" / "bronze" / "arrondissements_paris.csv"
DEFAULT_POPULATION_INPUT = PROJECT_ROOT / "data" / "bronze" / "population_paris.xlsx"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "silver" / "population_paris.csv"

PARIS_ARRONDISSEMENT_CODES = [f"751{index:02d}" for index in range(1, 21)]

ARR_CODE_COLUMN = "Num\u00e9ro d\u2019arrondissement INSEE"
ARR_SURFACE_COLUMN = "Surface"
ARR_NAME_COLUMN = "Nom de l\u2019arrondissement"

POP_COMMUNE_COLUMN = "Code commune"
POP_DEPARTEMENT_COLUMN = "Code d\u00e9partement"
POP_NAME_COLUMN = "Nom de la commune"
POP_VALUE_COLUMN = "Population municipale"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Concat\u00e8ne simplement population et superficies des arrondissements de Paris.",
    )
    parser.add_argument(
        "--arrondissements",
        type=Path,
        default=DEFAULT_ARRONDISSEMENTS_INPUT,
        help="Chemin du CSV des arrondissements (par d\u00e9faut data/bronze/arrondissements_paris.csv).",
    )
    parser.add_argument(
        "--population",
        type=Path,
        default=DEFAULT_POPULATION_INPUT,
        help="Chemin du fichier Excel population (par d\u00e9faut data/bronze/population_paris.xlsx).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Chemin du CSV de sortie (par d\u00e9faut data/silver/population_paris.csv).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Affiche le r\u00e9sultat au lieu de l'enregistrer.",
    )
    return parser.parse_args()


def load_arrondissements(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="cp1252", dtype=str)
    df["code_insee"] = df[ARR_CODE_COLUMN].astype(str).str.strip().str.zfill(5)
    df["superficie_km2"] = (
        pd.to_numeric(df[ARR_SURFACE_COLUMN], errors="coerce") / 1_000_000
    )
    df["nom_arrondissement"] = df[ARR_NAME_COLUMN].astype(str).str.strip()
    return df[["code_insee", "nom_arrondissement", "superficie_km2"]]


def load_population(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str, engine="openpyxl")
    df["code_insee"] = (
        df[POP_DEPARTEMENT_COLUMN].astype(str).str.strip().str.zfill(2)
        + df[POP_COMMUNE_COLUMN].astype(str).str.strip().str.zfill(3)
    )
    df["nom_standard"] = df[POP_NAME_COLUMN].astype(str).str.strip()
    df["population"] = pd.to_numeric(df[POP_VALUE_COLUMN], errors="coerce").astype("Int64")
    return df[["code_insee", "nom_standard", "population"]]


def prepare_dataset(arrondissements: pd.DataFrame, populations: pd.DataFrame) -> pd.DataFrame:
    merged = populations.merge(arrondissements, on="code_insee", how="inner")
    merged = merged[merged["code_insee"].isin(PARIS_ARRONDISSEMENT_CODES)]
    merged["densite"] = (
        merged["population"].astype("Float64") / merged["superficie_km2"].replace({0: pd.NA})
    ).astype("Float64")
    columns = ["code_insee", "nom_standard", "population", "superficie_km2", "densite"]
    result = merged[columns].sort_values("code_insee").reset_index(drop=True)
    return result


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> None:
    args = parse_arguments()
    arrondissements = load_arrondissements(args.arrondissements)
    populations = load_population(args.population)
    dataset = prepare_dataset(arrondissements, populations)

    if args.no_save:
        print(dataset)
        return

    save_dataframe(dataset, args.output)
    print(f"Donn\u00e9es enregistr\u00e9es dans {args.output} ({len(dataset)} lignes).")


if __name__ == "__main__":
    main()
