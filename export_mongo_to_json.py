#!/usr/bin/env python3
"""
Exporte la collection MongoDB transport_details en JSON
pour démontrer l'intégration de sources variées dans le Data Lake
(CSV depuis PostgreSQL/Gold + JSON depuis MongoDB)
"""
from pymongo import MongoClient
import json
from pathlib import Path

MONGO_URL = "mongodb://paris_admin:paris2024@localhost:27017/?authSource=admin"
MONGO_DB = "urban_data_explorer"
OUTPUT_PATH = Path("source/transport_details.json")

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]

docs = list(db.transport_details.find({}, {"_id": 0}))

OUTPUT_PATH.parent.mkdir(exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")

print(f"✓ {len(docs)} documents exportés vers {OUTPUT_PATH}")
