#!/usr/bin/env python3
"""
Correction des doublons de lignes métro/RER (ex: "14" et "14.0")
====================================================================
Nettoie PostgreSQL ET MongoDB pour avoir des listes de lignes propres,
sans doublons liés aux suffixes ".0".
"""

from sqlalchemy import create_engine, text
from pymongo import MongoClient
import pandas as pd

PG_URL = "postgresql://paris_admin:paris2024@localhost:5433/urban_data_explorer"
MONGO_URL = "mongodb://paris_admin:paris2024@localhost:27017/?authSource=admin"
MONGO_DB = "urban_data_explorer"


def nettoyer_lignes(lignes_str):
    """Nettoie une chaîne de lignes : enlève les .0 et les doublons, trie"""
    if pd.isna(lignes_str) or not lignes_str:
        return None, 0

    lignes = [l.strip() for l in str(lignes_str).split(',')]
    lignes_propres = set()

    for l in lignes:
        if not l or l.lower() == 'nan':
            continue
        # Enlever le suffixe ".0" (ex: "14.0" -> "14")
        if l.endswith('.0'):
            l = l[:-2]
        lignes_propres.add(l)

    # Trier : chiffres d'abord (numériquement), puis lettres
    chiffres = sorted([l for l in lignes_propres if l.isdigit()], key=int)
    lettres = sorted([l for l in lignes_propres if not l.isdigit()])
    lignes_finales = chiffres + lettres

    return ', '.join(lignes_finales), len(lignes_finales)


def main():
    print("=" * 70)
    print("CORRECTION DES LIGNES MÉTRO/RER (doublons .0)")
    print("=" * 70)

    # ── PostgreSQL ───────────────────────────────────────────
    print("\n[1/2] Correction dans PostgreSQL...")
    engine = create_engine(PG_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT arrondissement, lignes_metro, lignes_rer FROM arrondissements"))
        rows = result.mappings().all()

        for row in rows:
            lignes_metro_propres, nb_metro = nettoyer_lignes(row['lignes_metro'])
            lignes_rer_propres, nb_rer = nettoyer_lignes(row['lignes_rer'])

            conn.execute(
                text("""
                    UPDATE arrondissements
                    SET lignes_metro = :lignes_metro,
                        nb_lignes_metro = :nb_metro,
                        lignes_rer = :lignes_rer,
                        nb_lignes_rer = :nb_rer
                    WHERE arrondissement = :arr
                """),
                {
                    "lignes_metro": lignes_metro_propres,
                    "nb_metro": nb_metro,
                    "lignes_rer": lignes_rer_propres,
                    "nb_rer": nb_rer,
                    "arr": row['arrondissement']
                }
            )
            print(f"  Arr. {row['arrondissement']:2d} : métro {nb_metro} lignes ({lignes_metro_propres}) | RER {nb_rer} lignes ({lignes_rer_propres or '-'})")

        conn.commit()
    print("  ✓ PostgreSQL corrigé")

    # ── MongoDB ──────────────────────────────────────────────
    print("\n[2/2] Correction dans MongoDB (transport_details)...")
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB]

    for doc in mongo_db.transport_details.find():
        lignes_metro_nettoyees = []
        for l in doc['metro']['lignes']:
            if l.endswith('.0'):
                l = l[:-2]
            if l not in lignes_metro_nettoyees:
                lignes_metro_nettoyees.append(l)

        chiffres = sorted([l for l in lignes_metro_nettoyees if l.isdigit()], key=int)
        lettres = sorted([l for l in lignes_metro_nettoyees if not l.isdigit()])
        lignes_finales = chiffres + lettres

        mongo_db.transport_details.update_one(
            {"_id": doc["_id"]},
            {"$set": {"metro.lignes": lignes_finales}}
        )

    print(f"  ✓ MongoDB corrigé ({mongo_db.transport_details.count_documents({})} documents)")

    print(f"\n{'='*70}")
    print("✅ CORRECTION TERMINÉE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
