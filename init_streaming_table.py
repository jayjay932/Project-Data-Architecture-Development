#!/usr/bin/env python3
"""Crée la table streaming_dvf dans PostgreSQL"""
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://paris_admin:paris2024@localhost:5433/urban_data_explorer")

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS streaming_dvf (
            id                        SERIAL PRIMARY KEY,
            arrondissement            INTEGER,
            prix_m2_moyen_streaming   NUMERIC,
            valeur_moyenne_streaming  NUMERIC,
            nb_transactions_streaming INTEGER,
            batch_id                  INTEGER,
            timestamp_traitement      TIMESTAMP DEFAULT NOW()
        )
    """))
    conn.commit()
    print("✓ Table streaming_dvf créée dans PostgreSQL")
