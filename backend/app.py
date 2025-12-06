from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "gold_layer"
PRICE_DATA_PATH = DATA_DIR / "price_year.csv"
ALL_DATA_PATH = DATA_DIR / "all_data.csv"
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
ARRONDISSEMENTS_FILE = FRONTEND_DIR / "arrondissements.geojson"

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
ARROND_LABEL_TO_CODE = {label.lower(): code for code, label in ARRONDISSEMENTS.items()}
CITY_LABEL = "Paris (tous arrondissements)"
SURFACE_SEGMENTS = [
    ("lt_20", "< 20 m²", "part_surface_lt_20", "transactions_surface_lt_20"),
    ("bt_20_40", "20 - 40 m²", "part_surface_bt_20_40", "transactions_surface_bt_20_40"),
    ("bt_40_60", "40 - 60 m²", "part_surface_bt_40_60", "transactions_surface_bt_40_60"),
    ("bt_60_80", "60 - 80 m²", "part_surface_bt_60_80", "transactions_surface_bt_60_80"),
    (
        "bt_80_120",
        "80 - 120 m²",
        "part_surface_bt_80_120",
        "transactions_surface_bt_80_120",
    ),
    ("gt_120", "> 120 m²", "part_surface_gt_120", "transactions_surface_gt_120"),
]


@dataclass(frozen=True)
class PriceEntry:
    year: int
    median_price_per_sqm: float


@dataclass(frozen=True)
class MetricEntry:
    code_commune: str
    year: int
    prix_m2_median: Optional[float]
    prix_m2_median_prev_year: Optional[float]
    variation: Optional[float]
    revenu_median: Optional[float]
    tx_logement_sociaux: Optional[float]
    air_quality_global: Optional[str]
    densite_population: Optional[float]
    no2: Optional[float]
    o3: Optional[float]
    pm10: Optional[float]
    qual_no2: Optional[str]
    qual_o3: Optional[str]
    qual_pm10: Optional[str]
    transactions_total: Optional[int]
    transactions_studio_t1: Optional[int]
    transactions_t2: Optional[int]
    transactions_t3: Optional[int]
    transactions_t4: Optional[int]
    transactions_t5_plus: Optional[int]
    part_studio_t1: Optional[float]
    part_t2: Optional[float]
    part_t3: Optional[float]
    part_t4: Optional[float]
    part_t5_plus: Optional[float]
    transactions_surface_lt_20: Optional[int]
    transactions_surface_bt_20_40: Optional[int]
    transactions_surface_bt_40_60: Optional[int]
    transactions_surface_bt_60_80: Optional[int]
    transactions_surface_bt_80_120: Optional[int]
    transactions_surface_gt_120: Optional[int]
    part_surface_lt_20: Optional[float]
    part_surface_bt_20_40: Optional[float]
    part_surface_bt_40_60: Optional[float]
    part_surface_bt_60_80: Optional[float]
    part_surface_bt_80_120: Optional[float]
    part_surface_gt_120: Optional[float]


def parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    cleaned = str(value).strip().replace(",", ".")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def load_price_data(csv_path: Path) -> Dict[int, PriceEntry]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Price file not found: {csv_path}")

    prices: Dict[int, PriceEntry] = {}
    with csv_path.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for row in reader:
            try:
                year = int(row["annee"])
                median = float(row["prix_m2_median"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Mauvaise ligne dans {csv_path}: {row}") from exc
            prices[year] = PriceEntry(year=year, median_price_per_sqm=median)
    return prices


def load_all_metrics(csv_path: Path) -> Dict[Tuple[str, int], MetricEntry]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Gold-layer dataset introuvable: {csv_path}")

    metrics: Dict[Tuple[str, int], MetricEntry] = {}
    with csv_path.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for row in reader:
            code_commune = row["code_commune"].zfill(5)
            try:
                year = int(row["annee"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Année invalide pour {code_commune}: {row}") from exc

            entry = MetricEntry(
                code_commune=code_commune,
                year=year,
                prix_m2_median=parse_optional_float(row.get("prix_m2_median")),
                prix_m2_median_prev_year=parse_optional_float(
                    row.get("prix_m2_median_prev_year")
                ),
                variation=parse_optional_float(row.get("variation")),
                revenu_median=parse_optional_float(row.get("revenu_median")),
                tx_logement_sociaux=parse_optional_float(row.get("tx_logement_sociaux")),
                air_quality_global=parse_optional_string(row.get("air_quality_global")),
                densite_population=parse_optional_float(row.get("densite_population")),
                no2=parse_optional_float(row.get("no2")),
                o3=parse_optional_float(row.get("o3")),
                pm10=parse_optional_float(row.get("pm10")),
                qual_no2=parse_optional_string(row.get("qual_no2")),
                qual_o3=parse_optional_string(row.get("qual_o3")),
                qual_pm10=parse_optional_string(row.get("qual_pm10")),
                transactions_total=parse_optional_int(row.get("transactions_total")),
                transactions_studio_t1=parse_optional_int(row.get("transactions_studio_t1")),
                transactions_t2=parse_optional_int(row.get("transactions_t2")),
                transactions_t3=parse_optional_int(row.get("transactions_t3")),
                transactions_t4=parse_optional_int(row.get("transactions_t4")),
                transactions_t5_plus=parse_optional_int(row.get("transactions_t5_plus")),
                part_studio_t1=parse_optional_float(row.get("part_studio_t1")),
                part_t2=parse_optional_float(row.get("part_t2")),
                part_t3=parse_optional_float(row.get("part_t3")),
                part_t4=parse_optional_float(row.get("part_t4")),
                part_t5_plus=parse_optional_float(row.get("part_t5_plus")),
                transactions_surface_lt_20=parse_optional_int(
                    row.get("transactions_surface_lt_20")
                ),
                transactions_surface_bt_20_40=parse_optional_int(
                    row.get("transactions_surface_bt_20_40")
                ),
                transactions_surface_bt_40_60=parse_optional_int(
                    row.get("transactions_surface_bt_40_60")
                ),
                transactions_surface_bt_60_80=parse_optional_int(
                    row.get("transactions_surface_bt_60_80")
                ),
                transactions_surface_bt_80_120=parse_optional_int(
                    row.get("transactions_surface_bt_80_120")
                ),
                transactions_surface_gt_120=parse_optional_int(
                    row.get("transactions_surface_gt_120")
                ),
                part_surface_lt_20=parse_optional_float(row.get("part_surface_lt_20")),
                part_surface_bt_20_40=parse_optional_float(row.get("part_surface_bt_20_40")),
                part_surface_bt_40_60=parse_optional_float(row.get("part_surface_bt_40_60")),
                part_surface_bt_60_80=parse_optional_float(row.get("part_surface_bt_60_80")),
                part_surface_bt_80_120=parse_optional_float(row.get("part_surface_bt_80_120")),
                part_surface_gt_120=parse_optional_float(row.get("part_surface_gt_120")),
            )
            metrics[(code_commune, year)] = entry
    return metrics


def safe_mean(values: List[Optional[float]]) -> Optional[float]:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def safe_sum(values: List[Optional[float]]) -> Optional[float]:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid)


def most_common(values: List[Optional[str]]) -> Optional[str]:
    filtered = [value for value in values if value]
    if not filtered:
        return None
    return Counter(filtered).most_common(1)[0][0]


def compute_price_variations(prices: Dict[int, PriceEntry]) -> Dict[int, Optional[float]]:
    variations: Dict[int, Optional[float]] = {}
    for year in sorted(prices.keys()):
        prev_year = year - 1
        current = prices[year]
        previous = prices.get(prev_year)
        if not previous or previous.median_price_per_sqm == 0:
            variations[year] = None
            continue
        change = (
            (current.median_price_per_sqm - previous.median_price_per_sqm)
            / previous.median_price_per_sqm
        ) * 100
        variations[year] = round(change, 2)
    return variations


def build_city_metrics(
    metrics: Dict[Tuple[str, int], MetricEntry],
    prices: Dict[int, PriceEntry],
) -> Dict[int, MetricEntry]:
    per_year: Dict[int, List[MetricEntry]] = {}
    for entry in metrics.values():
        per_year.setdefault(entry.year, []).append(entry)

    price_variations = compute_price_variations(prices)
    city_metrics: Dict[int, MetricEntry] = {}

    for year, entries in per_year.items():
        total_transactions = safe_sum([entry.transactions_total for entry in entries])
        total_studio = safe_sum([entry.transactions_studio_t1 for entry in entries])
        total_t2 = safe_sum([entry.transactions_t2 for entry in entries])
        total_t3 = safe_sum([entry.transactions_t3 for entry in entries])
        total_t4 = safe_sum([entry.transactions_t4 for entry in entries])
        total_t5_plus = safe_sum([entry.transactions_t5_plus for entry in entries])
        total_surface_lt_20 = safe_sum(
            [entry.transactions_surface_lt_20 for entry in entries]
        )
        total_surface_bt_20_40 = safe_sum(
            [entry.transactions_surface_bt_20_40 for entry in entries]
        )
        total_surface_bt_40_60 = safe_sum(
            [entry.transactions_surface_bt_40_60 for entry in entries]
        )
        total_surface_bt_60_80 = safe_sum(
            [entry.transactions_surface_bt_60_80 for entry in entries]
        )
        total_surface_bt_80_120 = safe_sum(
            [entry.transactions_surface_bt_80_120 for entry in entries]
        )
        total_surface_gt_120 = safe_sum(
            [entry.transactions_surface_gt_120 for entry in entries]
        )

        def as_int(value: Optional[float]) -> Optional[int]:
            if value is None:
                return None
            return int(round(value))

        def compute_share(count: Optional[float]) -> Optional[float]:
            if total_transactions is None or not total_transactions:
                return None
            if count is None:
                return 0.0
            return round((count / total_transactions) * 100, 2)

        city_metrics[year] = MetricEntry(
            code_commune="all",
            year=year,
            prix_m2_median=prices.get(year).median_price_per_sqm
            if prices.get(year)
            else None,
            prix_m2_median_prev_year=prices.get(year - 1).median_price_per_sqm
            if prices.get(year - 1)
            else None,
            variation=price_variations.get(year),
            revenu_median=safe_mean([entry.revenu_median for entry in entries]),
            tx_logement_sociaux=safe_mean(
                [entry.tx_logement_sociaux for entry in entries]
            ),
            air_quality_global=most_common(
                [entry.air_quality_global for entry in entries]
            ),
            densite_population=safe_mean(
                [entry.densite_population for entry in entries]
            ),
            no2=safe_mean([entry.no2 for entry in entries]),
            o3=safe_mean([entry.o3 for entry in entries]),
            pm10=safe_mean([entry.pm10 for entry in entries]),
            qual_no2=most_common([entry.qual_no2 for entry in entries]),
            qual_o3=most_common([entry.qual_o3 for entry in entries]),
            qual_pm10=most_common([entry.qual_pm10 for entry in entries]),
            transactions_total=as_int(total_transactions),
            transactions_studio_t1=as_int(total_studio),
            transactions_t2=as_int(total_t2),
            transactions_t3=as_int(total_t3),
            transactions_t4=as_int(total_t4),
            transactions_t5_plus=as_int(total_t5_plus),
            part_studio_t1=compute_share(total_studio),
            part_t2=compute_share(total_t2),
            part_t3=compute_share(total_t3),
            part_t4=compute_share(total_t4),
            part_t5_plus=compute_share(total_t5_plus),
            transactions_surface_lt_20=as_int(total_surface_lt_20),
            transactions_surface_bt_20_40=as_int(total_surface_bt_20_40),
            transactions_surface_bt_40_60=as_int(total_surface_bt_40_60),
            transactions_surface_bt_60_80=as_int(total_surface_bt_60_80),
            transactions_surface_bt_80_120=as_int(total_surface_bt_80_120),
            transactions_surface_gt_120=as_int(total_surface_gt_120),
            part_surface_lt_20=compute_share(total_surface_lt_20),
            part_surface_bt_20_40=compute_share(total_surface_bt_20_40),
            part_surface_bt_40_60=compute_share(total_surface_bt_40_60),
            part_surface_bt_60_80=compute_share(total_surface_bt_60_80),
            part_surface_bt_80_120=compute_share(total_surface_bt_80_120),
            part_surface_gt_120=compute_share(total_surface_gt_120),
        )
    return city_metrics


def arrondissement_number_to_code(number: int) -> str:
    return f"751{number:02d}"


def normalize_arrondissement_code(raw_value: str) -> Optional[str]:
    if not raw_value:
        return None
    lowered = raw_value.strip().lower()
    if lowered in {"all", "tous", "tout", "paris"}:
        return "all"

    if raw_value in ARRONDISSEMENTS:
        return raw_value

    if lowered in ARROND_LABEL_TO_CODE:
        return ARROND_LABEL_TO_CODE[lowered]

    digits = "".join(ch for ch in raw_value if ch.isdigit())
    if digits:
        if len(digits) >= 5:
            candidate = digits[-5:]
            if candidate in ARRONDISSEMENTS:
                return candidate
        try:
            number = int(digits[-2:]) if len(digits) > 2 else int(digits)
        except ValueError:
            return None
        if 1 <= number <= len(ARRONDISSEMENTS):
            return arrondissement_number_to_code(number)
    return None


app = Flask(__name__)
CORS(app)
PRICE_DATA = load_price_data(PRICE_DATA_PATH)
METRICS_BY_KEY = load_all_metrics(ALL_DATA_PATH)
CITY_METRICS = build_city_metrics(METRICS_BY_KEY, PRICE_DATA)


@app.route("/api/price", methods=["GET"])
def get_price_by_year():
    year_param = request.args.get("year", type=int)
    if year_param is None:
        return jsonify({"error": "Paramètre 'year' requis (ex: /api/price?year=2022)."}), 400

    entry = PRICE_DATA.get(year_param)
    if not entry:
        return jsonify({"error": f"Aucune donnée trouvée pour {year_param}."}), 404

    return jsonify(
        {
            "year": entry.year,
            "median_price_per_sqm": entry.median_price_per_sqm,
            "currency": "EUR",
        }
    )


@app.route("/api/price/history", methods=["GET"])
def get_price_history():
    arrondissement_param = request.args.get("arrondissement", "all")
    normalized_code = normalize_arrondissement_code(arrondissement_param)
    if normalized_code is None:
        return (
            jsonify({"error": f"Arrondissement inconnu: {arrondissement_param}"}),
            400,
        )

    if normalized_code == "all":
        entries = sorted(CITY_METRICS.items())
        label = CITY_LABEL
    else:
        label = ARRONDISSEMENTS.get(normalized_code)
        entries = sorted(
            (
                (year, entry)
                for (code, year), entry in METRICS_BY_KEY.items()
                if code == normalized_code
            ),
            key=lambda item: item[0],
        )

    history = [
        {
            "year": year,
            "median_price_per_sqm": entry.prix_m2_median,
        }
        for year, entry in entries
        if entry.prix_m2_median is not None
    ]
    if not history:
        return jsonify({"error": "Aucune donnée trouvée pour ces paramètres."}), 404

    return jsonify({"prices": history, "currency": "EUR", "label": label})


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    year_param = request.args.get("year", type=int)
    arrondissement_param = request.args.get("arrondissement") or request.args.get(
        "code_commune"
    )

    if year_param is None or arrondissement_param is None:
        return jsonify({"error": "Paramètres 'year' et 'arrondissement' requis."}), 400

    normalized_code = normalize_arrondissement_code(arrondissement_param)
    if normalized_code is None:
        return jsonify({"error": f"Arrondissement inconnu: {arrondissement_param}"}), 400

    if normalized_code == "all":
        entry = CITY_METRICS.get(year_param)
    else:
        entry = METRICS_BY_KEY.get((normalized_code, year_param))

    if not entry:
        return jsonify({"error": "Aucune donnée trouvée pour ces paramètres."}), 404

    payload = asdict(entry)
    payload["label"] = (
        CITY_LABEL if normalized_code == "all" else ARRONDISSEMENTS.get(entry.code_commune)
    )
    return jsonify(payload)


@app.route("/api/typology", methods=["GET"])
def get_typology_breakdown():
    year_param = request.args.get("year", type=int)
    arrondissement_param = request.args.get("arrondissement") or request.args.get(
        "code_commune"
    )

    if year_param is None or arrondissement_param is None:
        return jsonify({"error": "Paramètres 'year' et 'arrondissement' requis."}), 400

    normalized_code = normalize_arrondissement_code(arrondissement_param)
    if normalized_code is None:
        return jsonify({"error": f"Arrondissement inconnu: {arrondissement_param}"}), 400

    if normalized_code == "all":
        entry = CITY_METRICS.get(year_param)
    else:
        entry = METRICS_BY_KEY.get((normalized_code, year_param))

    if not entry:
        return jsonify({"error": "Aucune donnée trouvée pour ces paramètres."}), 404

    label = CITY_LABEL if normalized_code == "all" else ARRONDISSEMENTS.get(entry.code_commune)
    segments_config = [
        ("studio_t1", "Studios / T1", entry.part_studio_t1, entry.transactions_studio_t1),
        ("t2", "T2", entry.part_t2, entry.transactions_t2),
        ("t3", "T3", entry.part_t3, entry.transactions_t3),
        ("t4", "T4", entry.part_t4, entry.transactions_t4),
        ("t5_plus", "T5 et +", entry.part_t5_plus, entry.transactions_t5_plus),
    ]

    segments = []
    for segment_id, segment_label, value, count in segments_config:
        segments.append(
            {
                "id": segment_id,
                "label": segment_label,
                "value": float(value) if value is not None else 0.0,
                "count": int(count) if count is not None else 0,
            }
        )

    return jsonify(
        {
            "label": label,
            "year": year_param,
            "total_transactions": int(entry.transactions_total or 0),
            "segments": segments,
        }
    )


@app.route("/api/surfaces", methods=["GET"])
def get_surface_breakdown():
    year_param = request.args.get("year", type=int)
    arrondissement_param = request.args.get("arrondissement") or request.args.get(
        "code_commune"
    )

    if year_param is None or arrondissement_param is None:
        return jsonify({"error": "Paramètres 'year' et 'arrondissement' requis."}), 400

    normalized_code = normalize_arrondissement_code(arrondissement_param)
    if normalized_code is None:
        return jsonify({"error": f"Arrondissement inconnu: {arrondissement_param}"}), 400

    if normalized_code == "all":
        entry = CITY_METRICS.get(year_param)
    else:
        entry = METRICS_BY_KEY.get((normalized_code, year_param))

    if not entry:
        return jsonify({"error": "Aucune donnée trouvée pour ces paramètres."}), 404

    label = CITY_LABEL if normalized_code == "all" else ARRONDISSEMENTS.get(entry.code_commune)
    segments = []
    for segment_id, segment_label, share_attr, count_attr in SURFACE_SEGMENTS:
        share_value = getattr(entry, share_attr)
        count_value = getattr(entry, count_attr)
        segments.append(
            {
                "id": segment_id,
                "label": segment_label,
                "value": float(share_value) if share_value is not None else 0.0,
                "count": int(count_value) if count_value is not None else 0,
            }
        )

    return jsonify(
        {
            "label": label,
            "year": year_param,
            "total_transactions": int(entry.transactions_total or 0),
            "segments": segments,
        }
    )


@app.route("/api/arrondissements", methods=["GET"])
def list_arrondissements():
    arr_list = [
        {"code_commune": code, "label": label}
        for code, label in ARRONDISSEMENTS.items()
    ]
    return jsonify(arr_list)


@app.route("/api/arrondissements.geojson", methods=["GET"])
def get_arrondissements_geojson():
    if not ARRONDISSEMENTS_FILE.exists():
        return jsonify({"error": f"Fichier {ARRONDISSEMENTS_FILE.name} introuvable."}), 404

    return send_from_directory(
        directory=ARRONDISSEMENTS_FILE.parent,
        path=ARRONDISSEMENTS_FILE.name,
        mimetype="application/geo+json",
    )


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path: str):
    target = (FRONTEND_DIR / path).resolve()
    try:
        target.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        abort(404)

    if target.is_dir():
        target = target / "index.html"
    if not target.exists():
        abort(404)

    relative_path = target.relative_to(FRONTEND_DIR).as_posix()
    return send_from_directory(FRONTEND_DIR, relative_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
