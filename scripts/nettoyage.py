#!/usr/bin/env python3
"""
Nettoyage des fichiers DVF pour Paris.

Fonctionnalités principales :
- suppression des colonnes entièrement vides connues
- conversion des types (dates, valeurs numériques, géolocalisation)
- filtrage des lignes à valeur foncière manquante ou nulle
- extraction des informations de lots dans un fichier séparé
- traitement d'un ou plusieurs fichiers CSV d'un dossier
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

# Colonnes DVF historiquement vides sur Paris
EMPTY_COLUMNS = [
    "ancien_code_commune",
    "ancien_nom_commune",
    "ancien_id_parcelle",
    "code_nature_culture_speciale",
    "nature_culture_speciale",
]

# Colonnes numériques à convertir si présentes
NUMERIC_COLUMNS = [
    "valeur_fonciere",
    "surface_reelle_bati",
    "surface_terrain",
    "lot1_surface_carrez",
    "lot2_surface_carrez",
    "lot3_surface_carrez",
    "lot4_surface_carrez",
    "lot5_surface_carrez",
    "longitude",
    "latitude",
]

# Couples (lot_numero, surface) à transformer en table longue
LOT_COLUMNS: List[Tuple[str, str]] = [
    ("lot1_numero", "lot1_surface_carrez"),
    ("lot2_numero", "lot2_surface_carrez"),
    ("lot3_numero", "lot3_surface_carrez"),
    ("lot4_numero", "lot4_surface_carrez"),
    ("lot5_numero", "lot5_surface_carrez"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nettoyage des jeux de données DVF (Paris).")
    parser.add_argument(
        "csv_paths",
        nargs="*",
        default=["data/bronze/75_2020.csv"],
        help="Chemins des fichiers CSV à nettoyer (défaut : data/bronze/75_2020.csv).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Nettoyer tous les fichiers correspondant au motif (--pattern) dans --source-dir.",
    )
    parser.add_argument(
        "--source-dir",
        default="data/bronze",
        help="Répertoire contenant les fichiers source (utilisé avec --all).",
    )
    parser.add_argument(
        "--pattern",
        default="75_*.csv",
        help="Motif de fichiers à traiter avec --all (défaut : 75_*.csv).",
    )
    parser.add_argument(
        "--output-dir",
        default="data/silver",
        help="Répertoire de sortie pour les fichiers nettoyés (défaut : data/silver).",
    )
    return parser.parse_args()


def to_float_series(series: pd.Series) -> pd.Series:
    """Nettoie une série numérique représentée en chaînes."""
    cleaned = (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[\s ]", "", regex=True)
        .replace({"nan": None, "None": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def build_lot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Transforme les colonnes lotX_* en table longue id_mutation / lot / surface."""
    lot_frames = []
    for numero_col, surface_col in LOT_COLUMNS:
        if numero_col in df.columns and surface_col in df.columns:
            subset = (
                df[["id_mutation", numero_col, surface_col]]
                .rename(columns={numero_col: "lot_numero", surface_col: "surface_carrez"})
            )
            lot_frames.append(subset)

    if not lot_frames:
        return pd.DataFrame(columns=["id_mutation", "lot_numero", "surface_carrez"])

    lots = pd.concat(lot_frames, ignore_index=True)
    lots["lot_numero"] = lots["lot_numero"].astype(str).str.strip()
    lots["surface_carrez"] = to_float_series(lots["surface_carrez"])
    lots = lots.dropna(subset=["lot_numero", "surface_carrez"])
    lots = lots[lots["lot_numero"] != ""]
    lots = lots[lots["surface_carrez"] > 0]
    return lots


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage et enrichissement du DataFrame principal."""
    df = df.drop_duplicates().copy()

    # Suppression des colonnes connues pour être vides
    cols_to_drop = [col for col in EMPTY_COLUMNS if col in df.columns and df[col].isna().all()]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Conversion date
    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")

    # Conversion des colonnes numériques
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = to_float_series(df[col])

    if "valeur_fonciere" in df.columns:
        df = df[df["valeur_fonciere"].notna() & (df["valeur_fonciere"] > 0)]

    if {"adresse_numero", "adresse_suffixe", "adresse_nom_voie"} <= set(df.columns):
        df["adresse_complete"] = (
            df["adresse_numero"].fillna("").astype(str).str.strip()
            + " "
            + df["adresse_suffixe"].fillna("").astype(str).str.strip()
            + " "
            + df["adresse_nom_voie"].fillna("").astype(str).str.strip()
        )
        df["adresse_complete"] = df["adresse_complete"].str.replace(r"\s+", " ", regex=True).str.title().str.strip()

    if "code_postal" in df.columns:
        df["code_postal"] = df["code_postal"].fillna("").astype(str).str.zfill(5)
    if "code_commune" in df.columns:
        df["code_commune"] = df["code_commune"].fillna("").astype(str).str.zfill(5)

    if {"longitude", "latitude"} <= set(df.columns):
        df = df[
            df["longitude"].between(2.25, 2.45, inclusive="both")
            & df["latitude"].between(48.80, 48.95, inclusive="both")
        ]

    return df


def process_file(csv_path: Path, output_dir: Path) -> None:
    raw = pd.read_csv(csv_path, dtype=str)
    lots_df = build_lot_table(raw)
    df = enrich_dataframe(raw)

    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = csv_path.stem

    df.to_csv(output_dir / f"{base_name}_clean.csv", index=False)
    lots_df.to_csv(output_dir / f"{base_name}_lots.csv", index=False)

    print(f"[OK] {csv_path} → {output_dir / f'{base_name}_clean.csv'}")


def determine_paths(args: argparse.Namespace) -> Iterable[Path]:
    if args.all:
        source_dir = Path(args.source_dir)
        return sorted(source_dir.glob(args.pattern))
    return [Path(p) for p in args.csv_paths]


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    csv_paths = list(determine_paths(args))
    if not csv_paths:
        raise FileNotFoundError("Aucun fichier CSV trouvé avec les paramètres fournis.")

    for path in csv_paths:
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")
        process_file(path, output_dir)


if __name__ == "__main__":
    main()

