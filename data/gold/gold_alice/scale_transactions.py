#!/usr/bin/env python3
"""
Ajoute des colonnes normalisées (min-max) et standardisées (z-score)
pour les variables numériques du fichier fusionné DVF.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NUMERIC_COLUMNS = [
    "valeur_fonciere",
    "surface_reelle_bati",
    "surface_terrain",
    "nombre_pieces_principales",
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalise et standardise les transactions DVF.")
    parser.add_argument(
        "--input",
        default="data/gold/transactions_paris_2020_2025.csv",
        help="Fichier fusionné d'entrée (défaut : data/gold/transactions_paris_2020_2025.csv).",
    )
    parser.add_argument(
        "--output",
        default="data/gold/transactions_paris_2020_2025_scaled.csv",
        help="Fichier de sortie contenant les colonnes normalisées/standardisées.",
    )
    return parser.parse_args()

def min_max(series: pd.Series) -> pd.Series:
    min_val = series.min()
    max_val = series.max()
    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(0, index=series.index)
    return (series - min_val) / (max_val - min_val)

def z_score(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if pd.isna(mean) or pd.isna(std) or std == 0:
        return pd.Series(0, index=series.index)
    return (series - mean) / std

def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            df[f"{col}_minmax"] = min_max(numeric_series)
            df[f"{col}_zscore"] = z_score(numeric_series)

    df.to_csv(output_path, index=False)
    print(f"[OK] Fichier avec colonnes normalisées/standardisées -> {output_path}")

if __name__ == "__main__":
    main()
