from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "gold_layer" / "price_year.csv"
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
ARRONDISSEMENTS_FILE = FRONTEND_DIR / "arrondissements.geojson"


@dataclass(frozen=True)
class PriceEntry:
    year: int
    median_price_per_sqm: float


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


app = Flask(__name__)
CORS(app)
PRICE_DATA = load_price_data(DATA_PATH)


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
        }
    )


@app.route("/api/arrondissements.geojson", methods=["GET"])
def get_arrondissements_geojson():
    if not ARRONDISSEMENTS_FILE.exists():
        return jsonify({"error": f"Fichier {ARRONDISSEMENTS_FILE.name} introuvable."}), 404

    return send_from_directory(
        directory=ARRONDISSEMENTS_FILE.parent,
        path=ARRONDISSEMENTS_FILE.name,
        mimetype="application/geo+json",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
