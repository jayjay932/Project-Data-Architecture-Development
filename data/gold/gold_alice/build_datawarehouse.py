#!/usr/bin/env python3
"""
Construit un petit entrepôt de données (fact/dimension) à partir des fichiers
présents dans data/silver.

Produits :
 - data/gold/warehouse/fact_transactions.csv
 - data/gold/warehouse/fact_lots.csv
 - data/gold/warehouse/dim_stats_commune.csv
 - data/gold/warehouse/dim_qualite_air.csv
 - data/gold/warehouse/dim_transports.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd


WAREHOUSE_DIR = Path("data/gold/warehouse")

ARR_ORDINAL = {
    1: "1er",
    2: "2e",
    3: "3e",
    4: "4e",
    5: "5e",
    6: "6e",
    7: "7e",
    8: "8e",
    9: "9e",
    10: "10e",
    11: "11e",
    12: "12e",
    13: "13e",
    14: "14e",
    15: "15e",
    16: "16e",
    17: "17e",
    18: "18e",
    19: "19e",
    20: "20e",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit les tables du mini-warehouse.")
    parser.add_argument(
        "--silver-dir",
        default="data/silver",
        help="Répertoire contenant les fichiers silver (défaut : data/silver).",
    )
    parser.add_argument(
        "--warehouse-dir",
        default=WAREHOUSE_DIR,
        help="Répertoire de sortie pour l'entrepôt (défaut : data/gold/warehouse).",
    )
    return parser.parse_args()


def list_files(directory: Path, pattern: str) -> Iterable[Path]:
    return sorted(directory.glob(pattern))


def infer_year(path: Path) -> str | None:
    for part in path.stem.split("_"):
        if part.isdigit() and len(part) == 4:
            return part
    return None


def build_fact_transactions(silver_dir: Path, warehouse_dir: Path) -> None:
    files = list_files(silver_dir, "*_clean.csv")
    if not files:
        raise FileNotFoundError(f"Aucun fichier *_clean.csv trouvé dans {silver_dir}")

    frames = []
    for file_path in files:
        df = pd.read_csv(file_path, dtype=str)
        year = infer_year(file_path)
        if year:
            df["annee_source"] = year
        df["fichier_source"] = file_path.name
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(warehouse_dir / "fact_transactions.csv", index=False)


def build_fact_lots(silver_dir: Path, warehouse_dir: Path) -> None:
    files = list_files(silver_dir, "*_lots.csv")
    if not files:
        raise FileNotFoundError(f"Aucun fichier *_lots.csv trouvé dans {silver_dir}")

    frames = []
    for file_path in files:
        df = pd.read_csv(file_path, dtype=str)
        year = infer_year(file_path)
        if year:
            df["annee_source"] = year
        df["fichier_source"] = file_path.name
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(warehouse_dir / "fact_lots.csv", index=False)


def build_dim_stats_commune(silver_dir: Path, warehouse_dir: Path) -> None:
    path = silver_dir / "stats_commune_2014_2020.csv"
    if not path.exists():
        raise FileNotFoundError(f"Fichier manquant : {path}")

    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "anneemut": "annee",
            "nom_commune": "nom_commune",
            "code_commune": "code_commune",
            "nbmut": "nombre_mutations",
            "nbmut_vente": "nombre_mutations_vente",
            "nbmut_appart": "nombre_appart",
            "nbmut_maison": "nombre_maison",
            "vf_ventem": "valeur_totale_mutations",
            "vf_ventea": "valeur_totale_appart",
            "vfmed_ventem": "valeur_mediane_mutations",
            "vfmed_ventea": "valeur_mediane_appart",
            "vfm2_ventea": "valeur_m2_appart",
            "POP_2018": "population_2018",
            "Nbre-menages_2018": "menages_2018",
            "Logement_2018": "logements_2018",
        }
    )
    df.to_csv(warehouse_dir / "dim_stats_commune.csv", index=False)


def build_dim_qualite_air(silver_dir: Path, warehouse_dir: Path) -> None:
    path = silver_dir / "air_quality_paris_final.csv"
    if not path.exists():
        raise FileNotFoundError(f"Fichier manquant : {path}")

    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "arrondissement_nom": "nom_commune",
            "ninsee": "code_commune",
            "qualite_air": "indice_global",
        }
    )
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["annee"] = df["date"].dt.year
    df["mois"] = df["date"].dt.month
    df.to_csv(warehouse_dir / "dim_qualite_air.csv", index=False)


def build_dim_transports(silver_dir: Path, warehouse_dir: Path) -> None:
    path = silver_dir / "arrondissements_lignes_metro_rer.csv"
    if not path.exists():
        raise FileNotFoundError(f"Fichier manquant : {path}")

    df = pd.read_csv(path, sep=";")
    df = df.rename(
        columns={
            "Arrondissement": "arrondissement_numero",
            "Nombre_Stations": "nombre_stations",
            "Trafic_Total": "trafic_total",
            "Nombre_Lignes_Metro": "nombre_lignes_metro",
            "Nombre_Lignes_RER": "nombre_lignes_rer",
            "Lignes_Metro": "lignes_metro",
            "Lignes_RER": "lignes_rer",
            "Toutes_Lignes": "lignes_toutes",
        }
    )
    df["arrondissement_numero"] = pd.to_numeric(df["arrondissement_numero"], errors="coerce").astype("Int64")
    df["code_commune"] = df["arrondissement_numero"].apply(lambda x: f"751{x:02d}" if pd.notna(x) else None)
    df["nom_commune"] = df["arrondissement_numero"].apply(
        lambda x: f"Paris {ARR_ORDINAL.get(int(x), '')} Arrondissement" if pd.notna(x) else None
    )
    df.to_csv(warehouse_dir / "dim_transports.csv", index=False)


def main() -> None:
    args = parse_args()
    silver_dir = Path(args.silver_dir)
    warehouse_dir = Path(args.warehouse_dir)
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    build_fact_transactions(silver_dir, warehouse_dir)
    build_fact_lots(silver_dir, warehouse_dir)
    build_dim_stats_commune(silver_dir, warehouse_dir)
    build_dim_qualite_air(silver_dir, warehouse_dir)
    build_dim_transports(silver_dir, warehouse_dir)

    print(f"[OK] Entrepôt construit dans {warehouse_dir}")


if __name__ == "__main__":
    main()

