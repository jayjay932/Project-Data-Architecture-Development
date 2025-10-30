#!/usr/bin/env python3
"""
Nettoyage du fichier agrégé 2014-2020 DVF par commune/arrondissement.

Objectifs :
- lire le CSV avec séparateur ';'
- sélectionner les colonnes utiles pour les analyses
- normaliser les noms de colonnes
- exporter vers data/silver/stats_commune_2014_2020.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_COLUMNS = [
    "anneemut",
    "Nom Officiel Commune / Arrondissement Municipal Majuscule",
    "Code Officiel Commune",
    "codgeo_2020",
    "nbmut",
    "nbmut_vente",
    "nbmut_appart",
    "nbmut_maison",
    "vf_ventem",
    "vf_ventea",
    "vfmed_ventem",
    "vfmed_ventea",
    "vfm2_ventea",
    "POP_2018",
    "Nbre-menages_2018",
    "Logement_2018",
]

COLUMN_RENAME = {
    "Nom Officiel Commune / Arrondissement Municipal Majuscule": "nom_commune",
    "Code Officiel Commune": "code_commune",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nettoyage du jeu agrégé DVF 2014-2020.")
    parser.add_argument(
        "--input",
        default="data/bronze/2014_2020_donnees-valeurs-foncieres-a-la-commune.csv",
        help="Chemin du fichier CSV source (défaut : data/bronze/2014_2020_donnees-valeurs-foncieres-a-la-commune.csv).",
    )
    parser.add_argument(
        "--output",
        default="data/silver/stats_commune_2014_2020.csv",
        help="Chemin du fichier CSV de sortie (défaut : data/silver/stats_commune_2014_2020.csv).",
    )
    parser.add_argument(
        "--columns",
        nargs="*",
        default=DEFAULT_COLUMNS,
        help="Liste des colonnes à conserver. Par défaut, un sous-ensemble pertinent est gardé.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, sep=";")

    keep_cols = [col for col in args.columns if col in df.columns]
    df = df[keep_cols].copy()

    df = df.rename(columns=COLUMN_RENAME)
    df["anneemut"] = df["anneemut"].astype(int)
    df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)

    float_cols = [
        "vf_ventem",
        "vf_ventea",
        "vfmed_ventem",
        "vfmed_ventea",
        "vfm2_ventea",
        "POP_2018",
        "Nbre-menages_2018",
        "Logement_2018",
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["anneemut", "code_commune"]).reset_index(drop=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] {input_path} -> {output_path}")


if __name__ == "__main__":
    main()

