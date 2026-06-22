#!/usr/bin/env python3
"""
Fusion v6 + v7 → gold final complet
=====================================
Prend le meilleur des deux versions :
- v7 : population réelle 2022, revenus, superficie, densité, 4 indicateurs composites
- v6 : prix_m2_stats_2020, type_dominant par année (2020-2025)
"""
import pandas as pd

# ── CHEMINS — adapter si besoin ──────────────────────────────
V6 = r"C:\Users\jason\Downloads\projet_data_architecture\data\gold\dashboard_arrondissements_paris6.csv"
V7 = r"C:\Users\jason\Downloads\projet_data_architecture\data\gold\dashboard_arrondissements_paris_final.csv"
SORTIE = r"C:\Users\jason\Downloads\projet_data_architecture\data\gold\dashboard_gold_complet.csv"

print("Chargement des fichiers...")
df_v6 = pd.read_csv(V6, sep=";", low_memory=False)
df_v7 = pd.read_csv(V7, sep=";", low_memory=False)

print(f"  v6 : {len(df_v6)} lignes × {len(df_v6.columns)} colonnes")
print(f"  v7 : {len(df_v7)} lignes × {len(df_v7.columns)} colonnes")

# ── Colonnes à récupérer depuis v6 ──────────────────────────
cols_v6 = [
    "Arrondissement",
    "prix_m2_stats_2020",
    "type_dominant_2020", "type_dominant_2021", "type_dominant_2022",
    "type_dominant_2023", "type_dominant_2024", "type_dominant_2025",
]

# Garder seulement celles qui existent dans v6
cols_v6_ok = [c for c in cols_v6 if c in df_v6.columns]
df_v6_slim = df_v6[cols_v6_ok].copy()

# ── Supprimer les colonnes erronées de v7 si présentes ──────
cols_supprimer_v7 = ["population_2018", "nb_menages_2018", "nb_logements_2018"]
df_v7 = df_v7.drop(columns=[c for c in cols_supprimer_v7 if c in df_v7.columns])

# ── Fusion ───────────────────────────────────────────────────
df_final = df_v7.merge(df_v6_slim, on="Arrondissement", how="left")

# ── Réorganiser : mettre les nouvelles colonnes après les données existantes
# Les colonnes clés à mettre en avant
cols_ordre_debut = [
    "Arrondissement",
    "nb_ventes_2020", "prix_median_2020", "prix_m2_median_2020",
    "nb_ventes_2021", "prix_median_2021", "prix_m2_median_2021",
    "nb_ventes_2022", "prix_median_2022", "prix_m2_median_2022",
    "nb_ventes_2023", "prix_median_2023", "prix_m2_median_2023",
    "nb_ventes_2024", "prix_median_2024", "prix_m2_median_2024",
    "nb_ventes_2025", "prix_median_2025", "prix_m2_median_2025",
]

# Toutes les autres colonnes dans l'ordre existant
autres = [c for c in df_final.columns if c not in cols_ordre_debut]
df_final = df_final[cols_ordre_debut + autres]

# ── Sauvegarde ───────────────────────────────────────────────
import os
os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
df_final.to_csv(SORTIE, index=False, sep=";", encoding="utf-8-sig")

print(f"\n✅ Gold complet sauvegardé → {SORTIE}")
print(f"   {len(df_final)} arrondissements × {len(df_final.columns)} colonnes")
print(f"\n   Colonnes clés présentes :")
cols_check = [
    "prix_m2_median_2024", "prix_m2_stats_2020",
    "type_dominant_2020", "type_dominant_2024",
    "nb_stations_metro", "trafic_total_metro", "lignes_metro",
    "no2_moyen", "population_2022", "revenu_median",
    "indice_accessibilite", "indice_tension_sociale",
    "indice_attractivite", "indice_pression_immo"
]
for col in cols_check:
    status = "✓" if col in df_final.columns else "✗"
    print(f"   {status} {col}")