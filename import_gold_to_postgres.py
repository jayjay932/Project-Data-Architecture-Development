#!/usr/bin/env python3
"""
Import du Gold CSV vers PostgreSQL
====================================
Crée la table arrondissements et importe toutes les données
du gold final dans PostgreSQL (conteneur Docker).
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ── Configuration de connexion ──────────────────────────────
# Doit correspondre au docker-compose.yml
PG_USER = "paris_admin"
PG_PASSWORD = "paris2024"
PG_HOST = "localhost"
PG_PORT = "5433"
PG_DB = "urban_data_explorer"

PG_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# ── Chemin du gold final ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
GOLD_CANDIDATES = [
    PROJECT_ROOT / "data" / "gold" / "dashboard_gold_complet.csv",
    PROJECT_ROOT / "data" / "gold" / "dashboard_arrondissements_paris_final.csv",
    PROJECT_ROOT / "data" / "gold" / "dashboard_arrondissements_paris7.csv",
]

GOLD_CSV = next((path for path in GOLD_CANDIDATES if path.exists()), GOLD_CANDIDATES[0])

TABLE_NAME = "arrondissements"


def main():
    print("=" * 70)
    print("IMPORT DU GOLD CSV → POSTGRESQL")
    print("=" * 70)

    # ── 1. Connexion ────────────────────────────────────────
    print(f"\n[1/4] Connexion à PostgreSQL ({PG_HOST}:{PG_PORT})...")
    try:
        engine = create_engine(PG_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  ✓ Connexion réussie")
    except Exception as e:
        print(f"  ✗ Erreur de connexion : {e}")
        print("  → Vérifie que 'docker ps' montre postgres-paris en 'healthy'")
        return

    # ── 2. Chargement du CSV ────────────────────────────────
    print(f"\n[2/4] Chargement du CSV ({GOLD_CSV.name})...")
    if not GOLD_CSV.exists():
        print(f"  ✗ Fichier introuvable : {GOLD_CSV}")
        return

    df = pd.read_csv(GOLD_CSV, sep=";", low_memory=False)
    print(f"  ✓ {len(df)} lignes × {len(df.columns)} colonnes chargées")

    # ── 3. Nettoyage des noms de colonnes pour SQL ──────────
    print("\n[3/4] Normalisation des noms de colonnes...")
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(".", "_", regex=False)
        .str.replace("é", "e", regex=False)
        .str.replace("è", "e", regex=False)
        .str.replace("'", "", regex=False)
        .str.replace(" ", "_", regex=False)
    )
    print(f"  ✓ Colonnes normalisées (ex: {df.columns[0]}, {df.columns[1]}...)")

    # ── 4. Import dans PostgreSQL ────────────────────────────
    print(f"\n[4/4] Import dans la table '{TABLE_NAME}'...")
    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",  # Écrase la table si elle existe déjà
        index=False,
        method="multi"
    )
    print(f"  ✓ {len(df)} arrondissements importés")

    # ── Vérification ──────────────────────────────────────────
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
        count = result.scalar()
        print(f"\n  Vérification : {count} lignes présentes dans PostgreSQL")

        # Ajouter une clé primaire pour optimiser les requêtes
        try:
            conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD PRIMARY KEY (arrondissement)"))
            conn.commit()
            print(f"  ✓ Clé primaire ajoutée sur 'arrondissement'")
        except Exception as e:
            print(f"  ⚠ Clé primaire déjà présente ou erreur : {e}")

    print(f"\n{'='*70}")
    print(f"✅ IMPORT TERMINÉ AVEC SUCCÈS")
    print(f"   Table : {TABLE_NAME}")
    print(f"   Connexion : {PG_URL.replace(PG_PASSWORD, '****')}")
    print(f"   Tu peux vérifier dans pgAdmin : http://localhost:5050")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
