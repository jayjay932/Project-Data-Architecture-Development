#!/usr/bin/env python3
"""
Préparation du jeu des taux de logements sociaux pour Paris.

Étapes :
- lecture du fichier SCSV encodé en CP437 (fourni par l'utilisateur)
- filtrage sur Paris/arrondissements (codes 75xxx)
- production des couches Bronze (brut filtré) et Silver (colonnes normalisées)
- génération d'une couche Gold dédiée à Alice (data/gold/gold_alice)
"""

from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path
from typing import Tuple

import pandas as pd

RAW_INPUT = Path("data/bronze/logements-sociaux-dans-les-communes_IDF.csv")
DEFAULT_BRONZE_OUTPUT = Path("data/bronze/logements_sociaux_paris.csv")
DEFAULT_SILVER_OUTPUT = Path("data/silver/logements_sociaux_paris.csv")
DEFAULT_GOLD_OUTPUT = Path("data/gold/gold_alice/logements_sociaux_paris_arrondissements.csv")
ARRONDISSEMENTS_REF = Path("data/bronze/arrondissements_paris.csv")

COLUMN_RENAME = {
    "Code Commune": "code_commune",
    "Département": "departement",
    "Région": "region",
    "code_region": "code_region",
    "Taux de logements sociaux (%)": "taux_logements_sociaux",
    "geom": "geom",
    "centroid": "centroid",
    "code_departement": "code_departement",
    "Nom Commune": "nom_commune",
    "epci": "epci",
    "code_epci": "code_epci",
}

ARRONDISSEMENT_RENAME = {
    "Identifiant séquentiel de l’arrondissement": "arrondissement_id",
    "Identifiant_arrondissement": "arrondissement_id",
    "Numéro d’arrondissement": "arrondissement_numero",
    "Numero_arrondissement": "arrondissement_numero",
    "Numéro d’arrondissement INSEE": "code_commune",
    "Code_INSEE": "code_commune",
    "Nom de l’arrondissement": "arrondissement_nom_court",
    "Nom_arrondissement": "arrondissement_nom_court",
    "Nom officiel de l’arrondissement": "arrondissement_nom_officiel",
    "Nom_officiel_arrondissement": "arrondissement_nom_officiel",
    "Surface": "surface_m2",
    "Périmètre": "perimetre_m",
    "Perimetre": "perimetre_m",
    "Geometry X Y": "centroid",
    "Geometry_X_Y": "centroid",
    "Geometry": "geometry",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit Bronze/Silver/Gold pour les taux de logements sociaux (Paris).")
    parser.add_argument("--input", default=RAW_INPUT, help="Chemin du fichier SCSV source.")
    parser.add_argument("--bronze-output", default=DEFAULT_BRONZE_OUTPUT, help="Fichier Bronze filtré.")
    parser.add_argument("--silver-output", default=DEFAULT_SILVER_OUTPUT, help="Fichier Silver nettoyé.")
    parser.add_argument("--gold-output", default=DEFAULT_GOLD_OUTPUT, help="Fichier Gold final (défaut : data/gold/gold_alice/...).")
    parser.add_argument("--arrondissements-ref", default=ARRONDISSEMENTS_REF, help="Référentiel des arrondissements de Paris.")
    parser.add_argument("--skip-gold", action="store_true", help="Ne pas générer la couche Gold.")
    return parser.parse_args()


def load_cp437_csv(path: Path) -> pd.DataFrame:
    """Lit un CSV encodé en CP437, nécessaire pour récupérer correctement les accents."""
    text = path.read_bytes().decode("cp437").replace("╫", "Î")
    return pd.read_csv(StringIO(text), sep=";", dtype=str)


def filter_paris_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Ne conserve que Paris et ses éventuels arrondissements (codes 75xxx)."""
    df = df.copy()
    df["Code Commune"] = df["Code Commune"].astype(str).str.strip()
    df["Nom Commune"] = df["Nom Commune"].astype(str).str.strip()
    df["code_departement"] = df["code_departement"].astype(str).str.zfill(2)

    mask = df["code_departement"] == "75"
    mask |= df["Code Commune"].str.startswith("75")
    mask |= df["Nom Commune"].str.fullmatch("Paris", case=False, na=False)

    paris_df = df[mask].copy()
    if paris_df.empty:
        raise ValueError("Aucune ligne correspondant à Paris n'a été trouvée dans le fichier source.")
    return paris_df


def parse_centroid(value: str) -> Tuple[float | None, float | None]:
    if not isinstance(value, str):
        return (None, None)
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 2:
        return (None, None)
    try:
        lat = float(parts[0])
        lon = float(parts[1])
        return (lat, lon)
    except ValueError:
        return (None, None)


def build_silver_df(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = bronze_df.rename(columns=COLUMN_RENAME).copy()
    df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
    df["code_departement"] = df["code_departement"].astype(str).str.zfill(2)
    df["nom_commune"] = df["nom_commune"].str.strip()
    df["departement"] = df["departement"].str.strip()
    df["region"] = df["region"].str.strip()

    taux_series = df["taux_logements_sociaux"].astype(str).str.replace(",", ".", regex=False)
    df["taux_logements_sociaux"] = pd.to_numeric(taux_series, errors="coerce")

    centroids = df["centroid"].apply(parse_centroid)
    df["centroid_lat"] = [lat for lat, _ in centroids]
    df["centroid_lon"] = [lon for _, lon in centroids]

    ordered_cols = [
        "code_commune",
        "nom_commune",
        "code_departement",
        "departement",
        "code_region",
        "region",
        "taux_logements_sociaux",
        "centroid_lat",
        "centroid_lon",
        "geom",
        "epci",
        "code_epci",
    ]
    df = df[[col for col in ordered_cols if col in df.columns]].sort_values("code_commune").reset_index(drop=True)
    return df


def load_arrondissements(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig").rename(columns=ARRONDISSEMENT_RENAME)
    df["arrondissement_numero"] = pd.to_numeric(df["arrondissement_numero"], errors="coerce").astype("Int64")
    df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
    df["surface_m2"] = pd.to_numeric(df["surface_m2"], errors="coerce")
    df["perimetre_m"] = pd.to_numeric(df["perimetre_m"], errors="coerce")

    centroids = df["centroid"].apply(parse_centroid)
    df["centroid_lat"] = [lat for lat, _ in centroids]
    df["centroid_lon"] = [lon for _, lon in centroids]
    return df


def build_gold_df(silver_df: pd.DataFrame, arr_df: pd.DataFrame) -> pd.DataFrame:
    """Produit un tableau Paris + arrondissements avec le taux de logements sociaux."""
    silver_df = silver_df.copy()
    arr_df = arr_df.copy()

    taux_lookup = silver_df.set_index("code_commune")["taux_logements_sociaux"].to_dict()
    fallback_value = taux_lookup.get("75056") or next(iter(taux_lookup.values()), None)

    arr_df["taux_logements_sociaux"] = arr_df["code_commune"].map(taux_lookup)
    if fallback_value is not None:
        arr_df["taux_logements_sociaux"] = arr_df["taux_logements_sociaux"].fillna(fallback_value)

    arr_df["territoire_type"] = "arrondissement"
    arr_df["nom_territoire"] = arr_df["arrondissement_nom_officiel"]
    arr_df["source_commune_code"] = "75056"

    city_df = silver_df.copy()
    city_df["territoire_type"] = "commune"
    city_df["arrondissement_numero"] = pd.NA
    city_df["arrondissement_id"] = pd.NA
    city_df["nom_territoire"] = city_df["nom_commune"]
    city_df["surface_m2"] = pd.NA
    city_df["perimetre_m"] = pd.NA
    city_df["geometry"] = city_df["geom"]
    city_df["source_commune_code"] = city_df["code_commune"]

    final_cols = [
        "territoire_type",
        "code_commune",
        "nom_territoire",
        "arrondissement_numero",
        "taux_logements_sociaux",
        "centroid_lat",
        "centroid_lon",
        "surface_m2",
        "perimetre_m",
        "geometry",
        "source_commune_code",
    ]

    arr_selected = arr_df.reindex(columns=final_cols)
    city_selected = city_df.reindex(columns=final_cols)
    gold = pd.concat([city_selected, arr_selected], ignore_index=True)
    return gold


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[OK] {path}")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    raw_df = load_cp437_csv(input_path)
    paris_df = filter_paris_rows(raw_df)
    save_dataframe(paris_df, Path(args.bronze_output))

    silver_df = build_silver_df(paris_df)
    save_dataframe(silver_df, Path(args.silver_output))

    if not args.skip_gold:
        arr_df = load_arrondissements(Path(args.arrondissements_ref))
        gold_df = build_gold_df(silver_df, arr_df)
        save_dataframe(gold_df, Path(args.gold_output))


if __name__ == "__main__":
    main()
