#!/usr/bin/env python3
"""
Import de données semi-structurées vers MongoDB
==================================================
Démontre l'usage NoSQL (C1.2) en stockant des données
dont la structure varie d'un arrondissement à l'autre :
  - transport_details : lignes métro/RER (structure variable)
  - typologie_historique : évolution T1-T5+ par année (imbriqué)
  - indicateurs_detail : indicateurs composites + explications
"""

from pymongo import MongoClient
from sqlalchemy import create_engine, text
import pandas as pd

# ── Configuration ────────────────────────────────────────────
MONGO_USER = "paris_admin"
MONGO_PASSWORD = "paris2024"
MONGO_HOST = "localhost"
MONGO_PORT = "27017"
MONGO_DB = "urban_data_explorer"

PG_USER = "paris_admin"
PG_PASSWORD = "paris2024"
PG_HOST = "localhost"
PG_PORT = "5433"
PG_DB = "urban_data_explorer"

MONGO_URL = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
PG_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"


def parse_lignes(lignes_str):
    """Parse une chaîne de lignes séparées par virgules en liste propre"""
    if pd.isna(lignes_str) or not lignes_str:
        return []
    lignes = [l.strip() for l in str(lignes_str).split(',')]
    return [l for l in lignes if l and l.lower() != 'nan']


def main():
    print("=" * 70)
    print("IMPORT DONNÉES SEMI-STRUCTURÉES → MONGODB")
    print("=" * 70)

    # ── Connexions ───────────────────────────────────────────
    print("\n[1/5] Connexion à PostgreSQL et MongoDB...")
    pg_engine = create_engine(PG_URL)
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB]
    print("  ✓ Connexions établies")

    # ── Charger les données depuis PostgreSQL ───────────────
    print("\n[2/5] Chargement des données depuis PostgreSQL...")
    df = pd.read_sql("SELECT * FROM arrondissements", pg_engine)
    print(f"  ✓ {len(df)} arrondissements chargés")

    # ── Collection 1 : transport_details ─────────────────────
    print("\n[3/5] Construction de la collection 'transport_details'...")
    transport_docs = []
    for _, row in df.iterrows():
        doc = {
            "arrondissement": int(row["arrondissement"]),
            "metro": {
                "nb_stations": int(row["nb_stations_metro"]) if pd.notna(row.get("nb_stations_metro")) else 0,
                "trafic_annuel": int(row["trafic_total_metro"]) if pd.notna(row.get("trafic_total_metro")) else 0,
                "lignes": parse_lignes(row.get("lignes_metro"))
            },
            "rer": {
                "nb_lignes": int(row["nb_lignes_rer"]) if pd.notna(row.get("nb_lignes_rer")) else 0,
                "lignes": parse_lignes(row.get("lignes_rer"))
            }
        }
        transport_docs.append(doc)

    mongo_db.transport_details.drop()
    mongo_db.transport_details.insert_many(transport_docs)
    print(f"  ✓ {len(transport_docs)} documents insérés dans 'transport_details'")

    # ── Collection 2 : typologie_historique (structure imbriquée) ──
    print("\n[4/5] Construction de la collection 'typologie_historique'...")
    typologie_docs = []
    annees = [2020, 2021, 2022, 2023, 2024, 2025]

    for _, row in df.iterrows():
        historique = {}
        for annee in annees:
            historique[str(annee)] = {
                "T1": {
                    "nombre": int(row[f"nb_t1_{annee}"]) if pd.notna(row.get(f"nb_t1_{annee}")) else None,
                    "pourcentage": float(row[f"pct_t1_{annee}"]) if pd.notna(row.get(f"pct_t1_{annee}")) else None
                },
                "T2": {
                    "nombre": int(row[f"nb_t2_{annee}"]) if pd.notna(row.get(f"nb_t2_{annee}")) else None,
                    "pourcentage": float(row[f"pct_t2_{annee}"]) if pd.notna(row.get(f"pct_t2_{annee}")) else None
                },
                "T3": {
                    "nombre": int(row[f"nb_t3_{annee}"]) if pd.notna(row.get(f"nb_t3_{annee}")) else None,
                    "pourcentage": float(row[f"pct_t3_{annee}"]) if pd.notna(row.get(f"pct_t3_{annee}")) else None
                },
                "T4": {
                    "nombre": int(row[f"nb_t4_{annee}"]) if pd.notna(row.get(f"nb_t4_{annee}")) else None,
                    "pourcentage": float(row[f"pct_t4_{annee}"]) if pd.notna(row.get(f"pct_t4_{annee}")) else None
                },
                "type_dominant": row.get(f"type_dominant_{annee}") if pd.notna(row.get(f"type_dominant_{annee}")) else None
            }

        doc = {
            "arrondissement": int(row["arrondissement"]),
            "historique": historique
        }
        typologie_docs.append(doc)

    mongo_db.typologie_historique.drop()
    mongo_db.typologie_historique.insert_many(typologie_docs)
    print(f"  ✓ {len(typologie_docs)} documents insérés dans 'typologie_historique'")

    # ── Collection 3 : indicateurs_detail ─────────────────────
    print("\n[5/5] Construction de la collection 'indicateurs_detail'...")
    indicateurs_docs = []
    for _, row in df.iterrows():
        doc = {
            "arrondissement": int(row["arrondissement"]),
            "indicateurs": {
                "accessibilite": {
                    "score": float(row["indice_accessibilite"]) if pd.notna(row.get("indice_accessibilite")) else None,
                    "ratio_effort_achat_annees": float(row["ratio_effort_achat"]) if pd.notna(row.get("ratio_effort_achat")) else None,
                    "sources": ["DVF (prix m2)", "FiLoSoFi (revenu median)"]
                },
                "tension_sociale": {
                    "score": float(row["indice_tension_sociale"]) if pd.notna(row.get("indice_tension_sociale")) else None,
                    "sources": ["DVF (prix m2)", "APUR (logements sociaux)"]
                },
                "attractivite": {
                    "score": float(row["indice_attractivite"]) if pd.notna(row.get("indice_attractivite")) else None,
                    "sources": ["RATP (trafic, lignes)", "DVF (prix m2)"]
                },
                "pression_immobiliere": {
                    "score": float(row["indice_pression_immo"]) if pd.notna(row.get("indice_pression_immo")) else None,
                    "sources": ["DVF (evolution prix, volume, typologie)"]
                }
            }
        }
        indicateurs_docs.append(doc)

    mongo_db.indicateurs_detail.drop()
    mongo_db.indicateurs_detail.insert_many(indicateurs_docs)
    print(f"  ✓ {len(indicateurs_docs)} documents insérés dans 'indicateurs_detail'")

    # ── Vérification ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print("✅ IMPORT MONGODB TERMINÉ")
    print(f"{'='*70}")
    print(f"\nCollections créées dans la base '{MONGO_DB}' :")
    for coll_name in mongo_db.list_collection_names():
        count = mongo_db[coll_name].count_documents({})
        print(f"  • {coll_name} : {count} documents")

    print(f"\nExemple de document (transport_details, arr. 1) :")
    exemple = mongo_db.transport_details.find_one({"arrondissement": 1}, {"_id": 0})
    import json
    print(json.dumps(exemple, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
