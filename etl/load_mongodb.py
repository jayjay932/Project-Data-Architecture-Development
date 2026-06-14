from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

try:
    from pymongo import MongoClient, UpdateOne
except ImportError:
    MongoClient = None
    UpdateOne = None


ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "data" / "gold_layer"
ALL_DATA_PATH = GOLD_DIR / "all_data.csv"
PRICE_DATA_PATH = GOLD_DIR / "price_year.csv"

ARRONDISSEMENT_LABELS = [
    "1er arrondissement",
    "2e arrondissement",
    "3e arrondissement",
    "4e arrondissement",
    "5e arrondissement",
    "6e arrondissement",
    "7e arrondissement",
    "8e arrondissement",
    "9e arrondissement",
    "10e arrondissement",
    "11e arrondissement",
    "12e arrondissement",
    "13e arrondissement",
    "14e arrondissement",
    "15e arrondissement",
    "16e arrondissement",
    "17e arrondissement",
    "18e arrondissement",
    "19e arrondissement",
    "20e arrondissement",
]
ARRONDISSEMENTS = {
    f"751{i:02d}": label for i, label in enumerate(ARRONDISSEMENT_LABELS, start=1)
}
CITY_LABEL = "Paris (tous arrondissements)"

INT_FIELDS = [
    "transactions_total",
    "transactions_studio_t1",
    "transactions_t2",
    "transactions_t3",
    "transactions_t4",
    "transactions_t5_plus",
    "transactions_surface_lt_20",
    "transactions_surface_bt_20_40",
    "transactions_surface_bt_40_60",
    "transactions_surface_bt_60_80",
    "transactions_surface_bt_80_120",
    "transactions_surface_gt_120",
]
FLOAT_FIELDS = [
    "prix_m2_median",
    "prix_m2_median_prev_year",
    "variation",
    "revenu_median",
    "tx_logement_sociaux",
    "densite_population",
    "no2",
    "o3",
    "pm10",
    "part_studio_t1",
    "part_t2",
    "part_t3",
    "part_t4",
    "part_t5_plus",
    "part_surface_lt_20",
    "part_surface_bt_20_40",
    "part_surface_bt_40_60",
    "part_surface_bt_60_80",
    "part_surface_bt_80_120",
    "part_surface_gt_120",
]
STRING_FIELDS = ["air_quality_global", "qual_no2", "qual_o3", "qual_pm10"]
TYPOLOGY_COUNT_FIELDS = [
    "transactions_studio_t1",
    "transactions_t2",
    "transactions_t3",
    "transactions_t4",
    "transactions_t5_plus",
]
SURFACE_COUNT_FIELDS = [
    "transactions_surface_lt_20",
    "transactions_surface_bt_20_40",
    "transactions_surface_bt_40_60",
    "transactions_surface_bt_60_80",
    "transactions_surface_bt_80_120",
    "transactions_surface_gt_120",
]


def normalize_code(value) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned.zfill(5)
    if pd.isna(value):
        raise ValueError("code_commune manquant")
    return str(int(value)).zfill(5)


def to_optional_float(value) -> Optional[float]:
    if pd.isna(value):
        return None
    return float(value)


def to_optional_int(value) -> Optional[int]:
    if pd.isna(value):
        return None
    return int(float(value))


def to_optional_string(value) -> Optional[str]:
    if pd.isna(value):
        return None
    cleaned = str(value).strip()
    return cleaned or None


def read_gold_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    dataframe = pd.read_csv(path, sep=";", encoding="utf-8")
    if "code_commune" in dataframe.columns:
        dataframe["code_commune"] = dataframe["code_commune"].apply(normalize_code)
    return dataframe


def load_price_lookup(path: Path) -> Dict[int, float]:
    if not path.exists():
        raise FileNotFoundError(path)
    dataframe = pd.read_csv(path, sep=";", encoding="utf-8")
    return {
        int(row["annee"]): float(row["prix_m2_median"])
        for _, row in dataframe.iterrows()
        if not pd.isna(row["prix_m2_median"])
    }


def compute_price_variations(prices: Dict[int, float]) -> Dict[int, Optional[float]]:
    variations: Dict[int, Optional[float]] = {}
    for year in sorted(prices.keys()):
        previous = prices.get(year - 1)
        current = prices[year]
        if previous in {None, 0}:
            variations[year] = None
            continue
        variations[year] = round(((current - previous) / previous) * 100, 2)
    return variations


def safe_sum(values: Iterable[Optional[float]]) -> Optional[float]:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return float(sum(valid_values))


def safe_mean(values: Iterable[Optional[float]]) -> Optional[float]:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return float(sum(valid_values) / len(valid_values))


def most_common(values: Iterable[Optional[str]]) -> Optional[str]:
    filtered = [value for value in values if value]
    if not filtered:
        return None
    return Counter(filtered).most_common(1)[0][0]


def build_metric_document(record: pd.Series) -> Dict[str, object]:
    code_commune = normalize_code(record["code_commune"])
    year = int(record["annee"])
    document: Dict[str, object] = {
        "_id": f"{code_commune}_{year}",
        "code_commune": code_commune,
        "year": year,
        "label": ARRONDISSEMENTS.get(code_commune),
        "scope": "arrondissement",
    }

    for field_name in FLOAT_FIELDS:
        document[field_name] = to_optional_float(record.get(field_name))
    for field_name in INT_FIELDS:
        document[field_name] = to_optional_int(record.get(field_name))
    for field_name in STRING_FIELDS:
        document[field_name] = to_optional_string(record.get(field_name))

    return document


def build_city_documents(metrics_df: pd.DataFrame, prices: Dict[int, float]) -> list[Dict[str, object]]:
    variations = compute_price_variations(prices)
    documents: list[Dict[str, object]] = []

    for year, group in metrics_df.groupby("annee"):
        year = int(year)
        total_transactions = safe_sum(
            [to_optional_int(value) for value in group["transactions_total"].tolist()]
        )
        totals = {
            field_name: safe_sum(
                [to_optional_int(value) for value in group[field_name].tolist()]
            )
            for field_name in TYPOLOGY_COUNT_FIELDS + SURFACE_COUNT_FIELDS
        }

        def as_int(value: Optional[float]) -> Optional[int]:
            if value is None:
                return None
            return int(round(value))

        def compute_share(count: Optional[float]) -> Optional[float]:
            if total_transactions in {None, 0}:
                return None
            if count is None:
                return 0.0
            return round((count / total_transactions) * 100, 2)

        document: Dict[str, object] = {
            "_id": f"all_{year}",
            "code_commune": "all",
            "year": year,
            "label": CITY_LABEL,
            "scope": "city",
            "prix_m2_median": prices.get(year),
            "prix_m2_median_prev_year": prices.get(year - 1),
            "variation": variations.get(year),
            "revenu_median": safe_mean(
                [to_optional_float(value) for value in group["revenu_median"].tolist()]
            ),
            "tx_logement_sociaux": safe_mean(
                [to_optional_float(value) for value in group["tx_logement_sociaux"].tolist()]
            ),
            "air_quality_global": most_common(
                [to_optional_string(value) for value in group["air_quality_global"].tolist()]
            ),
            "densite_population": safe_mean(
                [to_optional_float(value) for value in group["densite_population"].tolist()]
            ),
            "no2": safe_mean([to_optional_float(value) for value in group["no2"].tolist()]),
            "o3": safe_mean([to_optional_float(value) for value in group["o3"].tolist()]),
            "pm10": safe_mean([to_optional_float(value) for value in group["pm10"].tolist()]),
            "qual_no2": most_common(
                [to_optional_string(value) for value in group["qual_no2"].tolist()]
            ),
            "qual_o3": most_common(
                [to_optional_string(value) for value in group["qual_o3"].tolist()]
            ),
            "qual_pm10": most_common(
                [to_optional_string(value) for value in group["qual_pm10"].tolist()]
            ),
            "transactions_total": as_int(total_transactions),
            "transactions_studio_t1": as_int(totals["transactions_studio_t1"]),
            "transactions_t2": as_int(totals["transactions_t2"]),
            "transactions_t3": as_int(totals["transactions_t3"]),
            "transactions_t4": as_int(totals["transactions_t4"]),
            "transactions_t5_plus": as_int(totals["transactions_t5_plus"]),
            "part_studio_t1": compute_share(totals["transactions_studio_t1"]),
            "part_t2": compute_share(totals["transactions_t2"]),
            "part_t3": compute_share(totals["transactions_t3"]),
            "part_t4": compute_share(totals["transactions_t4"]),
            "part_t5_plus": compute_share(totals["transactions_t5_plus"]),
            "transactions_surface_lt_20": as_int(totals["transactions_surface_lt_20"]),
            "transactions_surface_bt_20_40": as_int(
                totals["transactions_surface_bt_20_40"]
            ),
            "transactions_surface_bt_40_60": as_int(
                totals["transactions_surface_bt_40_60"]
            ),
            "transactions_surface_bt_60_80": as_int(
                totals["transactions_surface_bt_60_80"]
            ),
            "transactions_surface_bt_80_120": as_int(
                totals["transactions_surface_bt_80_120"]
            ),
            "transactions_surface_gt_120": as_int(totals["transactions_surface_gt_120"]),
            "part_surface_lt_20": compute_share(totals["transactions_surface_lt_20"]),
            "part_surface_bt_20_40": compute_share(
                totals["transactions_surface_bt_20_40"]
            ),
            "part_surface_bt_40_60": compute_share(
                totals["transactions_surface_bt_40_60"]
            ),
            "part_surface_bt_60_80": compute_share(
                totals["transactions_surface_bt_60_80"]
            ),
            "part_surface_bt_80_120": compute_share(
                totals["transactions_surface_bt_80_120"]
            ),
            "part_surface_gt_120": compute_share(totals["transactions_surface_gt_120"]),
        }
        documents.append(document)

    return documents


def load_documents() -> list[Dict[str, object]]:
    metrics_df = read_gold_dataframe(ALL_DATA_PATH)
    prices = load_price_lookup(PRICE_DATA_PATH)
    arrondissement_docs = [
        build_metric_document(record) for _, record in metrics_df.iterrows()
    ]
    city_docs = build_city_documents(metrics_df, prices)
    return arrondissement_docs + city_docs


def main():
    parser = argparse.ArgumentParser(
        description="Charge la couche gold dans MongoDB pour Urban Data Explorer."
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Supprime la collection cible avant le chargement.",
    )
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        help="URI MongoDB.",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("MONGODB_DB", "urban_data_explorer"),
        help="Base MongoDB cible.",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("MONGODB_COLLECTION", "metrics_yearly"),
        help="Collection MongoDB cible.",
    )
    args = parser.parse_args()

    if MongoClient is None or UpdateOne is None:
        raise RuntimeError(
            "Le chargement MongoDB requiert pymongo. Installez les dépendances de requirements.txt."
        )

    documents = load_documents()
    client = MongoClient(args.uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    collection = client[args.db][args.collection]

    if args.drop:
        collection.drop()

    collection.create_index([("code_commune", 1), ("year", 1)], unique=True)
    collection.create_index([("year", 1)])

    operations = [
        UpdateOne({"_id": document["_id"]}, {"$set": document}, upsert=True)
        for document in documents
    ]
    if operations:
        result = collection.bulk_write(operations, ordered=False)
        print(
            "Chargement MongoDB termine: "
            f"{len(documents)} documents, "
            f"{result.upserted_count} upserts, "
            f"{result.modified_count} modifications."
        )
    else:
        print("Aucun document a charger.")


if __name__ == "__main__":
    main()
