#!/usr/bin/env python3
"""
Script d'agrégation complète des données par arrondissement de Paris
Version finale enrichie avec :
  - Vraies données démographiques INSEE 2022
  - Revenus médians FiLoSoFi 2018
  - 4 indicateurs composites
"""

import pandas as pd
import numpy as np
import re
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

print("=" * 100)
print("CRÉATION DU DASHBOARD COMPLET PAR ARRONDISSEMENT - PARIS")
print("=" * 100)

# ============================================================================
# CONFIGURATION — modifie ces chemins si besoin
# ============================================================================

SILVER_PATH    = r"C:\Users\jason\Downloads\projet_data_architecture\data\silver"
BRONZE_PATH    = r"C:\Users\jason\Downloads\projet_data_architecture\data\bronze"
FICHIER_REVENUS = r"C:\Users\jason\Downloads\projet_data_architecture\data\bronze\BASE_TD_FILO_DEC_IRIS_2018.xlsx"
FICHIER_SORTIE = r"C:\Users\jason\Downloads\projet_data_architecture\data\gold\dashboard_arrondissements_paris_final.csv"

ANNEES = [2020, 2021, 2022, 2023, 2024, 2025]

# ============================================================================
# DONNÉES DE RÉFÉRENCE
# ============================================================================

POPULATION_2022 = {
    1:16266, 2:21559, 3:34576, 4:28088, 5:58850,
    6:41100, 7:51367, 8:36808, 9:59555, 10:90372,
    11:147476, 12:140694, 13:181557, 14:135964, 15:233392,
    16:165446, 17:167288, 18:195104, 19:184038, 20:195814,
}
NB_MENAGES_2022 = {
    1:9050, 2:11730, 3:18100, 4:14900, 5:29400,
    6:20800, 7:26200, 8:19900, 9:30500, 10:45800,
    11:74200, 12:70800, 13:91000, 14:68400, 15:117200,
    16:83200, 17:84100, 18:97800, 19:91500, 20:97200,
}
NB_LOGEMENTS_2022 = {
    1:10200, 2:13100, 3:20300, 4:16700, 5:33000,
    6:23200, 7:29400, 8:22300, 9:34300, 10:51500,
    11:83400, 12:79500, 13:102200, 14:76900, 15:131800,
    16:93500, 17:94500, 18:110200, 19:103200, 20:109400,
}
SUPERFICIE_KM2 = {
    1:1.83, 2:0.99, 3:1.17, 4:1.60, 5:2.54,
    6:2.15, 7:4.09, 8:3.88, 9:2.18, 10:2.89,
    11:3.67, 12:16.32, 13:7.15, 14:5.64, 15:8.48,
    16:16.31, 17:5.67, 18:6.01, 19:6.79, 20:5.98,
}
LOGEMENTS_SOCIAUX_APUR = {
    1:{"nb":1307,"pct":12.5}, 2:{"nb":893,"pct":6.7},
    3:{"nb":1838,"pct":9.0},  4:{"nb":2553,"pct":14.9},
    5:{"nb":3267,"pct":9.9},  6:{"nb":959,"pct":3.7},
    7:{"nb":904,"pct":2.7},   8:{"nb":955,"pct":3.9},
    9:{"nb":2660,"pct":7.4},  10:{"nb":8543,"pct":17.2},
    11:{"nb":13176,"pct":15.5}, 12:{"nb":20177,"pct":27.4},
    13:{"nb":39162,"pct":43.8}, 14:{"nb":22500,"pct":30.9},
    15:{"nb":26183,"pct":20.6}, 16:{"nb":6304,"pct":6.6},
    17:{"nb":16711,"pct":17.6}, 18:{"nb":25697,"pct":25.3},
    19:{"nb":38390,"pct":46.0}, 20:{"nb":39727,"pct":43.6},
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def extraire_arrondissement(code_postal):
    if pd.isna(code_postal): return None
    code = str(int(code_postal)) if isinstance(code_postal, float) else str(code_postal)
    if code.startswith('75') and len(code) == 5:
        arr = int(code[-2:])
        return arr if 1 <= arr <= 20 else None
    return None

def extraire_arrondissement_nom(nom):
    if pd.isna(nom): return None
    match = re.search(r'(\d+)[eér]', str(nom))
    if match:
        arr = int(match.group(1))
        return arr if 1 <= arr <= 20 else None
    return None

def extraire_arrondissement_insee(code):
    if pd.isna(code): return None
    code = str(int(code)) if isinstance(code, float) else str(code)
    if code.startswith('751') and len(code) == 5:
        arr = int(code[-2:])
        return arr if 1 <= arr <= 20 else None
    return None

def piece_to_typologie(n):
    if pd.isna(n): return None
    try: n = int(n)
    except: return None
    if n <= 0: return None
    if n == 1: return "T1"
    if n == 2: return "T2"
    if n == 3: return "T3"
    if n == 4: return "T4"
    return "T5plus"

def normaliser(series, inverse=False):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([5.0]*len(series), index=series.index)
    score = (series - mn) / (mx - mn) * 10
    return (10 - score) if inverse else score

# ============================================================================
# ÉTAPE 1 : DONNÉES IMMOBILIÈRES (2020-2025)
# ============================================================================

print("\nÉTAPE 1 : Chargement des données immobilières...")

donnees_immo_par_annee = {}

for annee in ANNEES:
    fichier_clean = f"{SILVER_PATH}\\75_{annee}_clean.csv"
    fichier_lots  = f"{SILVER_PATH}\\75_{annee}_lots.csv"
    try:
        df_clean = pd.read_csv(fichier_clean, sep=",", low_memory=False)
        print(f"  ✓ {annee} : {len(df_clean):,} lignes")
        if "arrondissement" not in df_clean.columns:
            if "code_postal" in df_clean.columns:
                df_clean["arrondissement"] = df_clean["code_postal"].apply(extraire_arrondissement)
            elif "nom_commune" in df_clean.columns:
                df_clean["arrondissement"] = df_clean["nom_commune"].apply(extraire_arrondissement_nom)
        df_clean = df_clean[df_clean["arrondissement"].notna()].copy()
        df_clean["arrondissement"] = df_clean["arrondissement"].astype(int)
        try:
            df_lots = pd.read_csv(fichier_lots, sep=",", low_memory=False)
            if "id_mutation" in df_clean.columns:
                df_clean = df_clean.merge(df_lots[["id_mutation","surface_carrez"]].drop_duplicates(), on="id_mutation", how="left")
        except: pass
        donnees_immo_par_annee[annee] = df_clean
    except Exception as e:
        print(f"  ⚠ {annee} non chargé : {e}")

# ============================================================================
# ÉTAPE 2 : AGRÉGATION IMMOBILIÈRE
# ============================================================================

print("\nÉTAPE 2 : Agrégation immobilière...")

resultats = {arr: {"Arrondissement": arr} for arr in range(1, 21)}

for annee in ANNEES:
    if annee not in donnees_immo_par_annee: continue
    df = donnees_immo_par_annee[annee].copy()
    if "nature_mutation" in df.columns:
        df = df[df["nature_mutation"] == "Vente"]
    for arr in range(1, 21):
        df_arr = df[df["arrondissement"] == arr].copy()
        resultats[arr][f"nb_ventes_{annee}"] = len(df_arr)
        if len(df_arr) == 0:
            resultats[arr][f"prix_median_{annee}"] = None
            resultats[arr][f"prix_m2_median_{annee}"] = None
            continue
        if "valeur_fonciere" in df_arr.columns:
            prix = df_arr["valeur_fonciere"].dropna()
            prix = prix[(prix > 10000) & (prix < 10_000_000)]
            resultats[arr][f"prix_median_{annee}"] = int(prix.median()) if len(prix) > 0 else None
        df_appart = df_arr[df_arr["type_local"] == "Appartement"] if "type_local" in df_arr.columns else df_arr
        m2_list = []
        for _, row in df_appart.iterrows():
            vf = row.get("valeur_fonciere")
            sr = row.get("surface_reelle_bati")
            sc = row.get("surface_carrez")
            if pd.notna(vf):
                surf = sr if pd.notna(sr) and sr > 0 else (sc if pd.notna(sc) and sc > 0 else None)
                if surf:
                    pm2 = vf / surf
                    if 3000 < pm2 < 50000: m2_list.append(pm2)
        resultats[arr][f"prix_m2_median_{annee}"] = int(np.median(m2_list)) if m2_list else None

# ============================================================================
# ÉTAPE 3 : ANALYSE DES TYPES DE LOCAUX
# ============================================================================

print("\nÉTAPE 3 : Analyse des types de locaux...")

for annee in ANNEES:
    if annee not in donnees_immo_par_annee: continue
    df_annee = donnees_immo_par_annee[annee].copy()
    if "nature_mutation" in df_annee.columns:
        df_annee = df_annee[df_annee["nature_mutation"] == "Vente"]
    for arr in range(1, 21):
        df_arr = df_annee[df_annee["arrondissement"] == arr].copy()
        if len(df_arr) == 0 or "type_local" not in df_arr.columns: continue
        type_counts = df_arr["type_local"].value_counts()
        total_ventes = len(df_arr)
        for type_local, count in type_counts.items():
            if pd.isna(type_local): continue
            if type_local == "Appartement": type_clean = "appartement"
            elif type_local == "Maison": type_clean = "maison"
            else: type_clean = type_local.lower().replace(" ","_").replace("/","_")
            pct = (count / total_ventes) * 100 if total_ventes > 0 else 0.0
            resultats[arr][f"nb_{type_clean}_{annee}"] = int(count)
            resultats[arr][f"pct_{type_clean}_{annee}"] = round(pct, 1)
        if len(type_counts) > 0:
            resultats[arr][f"type_dominant_{annee}"] = type_counts.index[0]

# ============================================================================
# ÉTAPE 4 : TYPOLOGIE PAR PIÈCES (T1-T5+)
# ============================================================================

print("\nÉTAPE 4 : Typologie par pièces...")

for annee in ANNEES:
    if annee not in donnees_immo_par_annee: continue
    df_typo = donnees_immo_par_annee[annee].copy()
    if "nombre_pieces_principales" not in df_typo.columns: continue
    if "type_local" in df_typo.columns:
        df_typo = df_typo[df_typo["type_local"].isin(["Appartement","Maison"])].copy()
    df_typo["typologie"] = df_typo["nombre_pieces_principales"].apply(piece_to_typologie)
    for arr in range(1, 21):
        df_arr = df_typo[df_typo["arrondissement"] == arr].copy()
        if len(df_arr) == 0: continue
        total = len(df_arr)
        counts = df_arr["typologie"].value_counts()
        for t in ["T1","T2","T3","T4","T5plus"]:
            nb = int(counts.get(t, 0))
            resultats[arr][f"nb_{t}_{annee}"] = nb
            resultats[arr][f"pct_{t}_{annee}"] = round(nb/total*100,1) if total > 0 else 0.0
        if "type_local" in df_arr.columns:
            nb_maison = len(df_arr[df_arr["type_local"]=="Maison"])
            resultats[arr][f"nb_maison_{annee}"] = nb_maison
            resultats[arr][f"pct_maison_{annee}"] = round(nb_maison/total*100,1) if total > 0 else 0.0

# ============================================================================
# ÉTAPE 5 : ÉVOLUTIONS TEMPORELLES
# ============================================================================

print("\nÉTAPE 5 : Évolutions temporelles...")

for arr in range(1, 21):
    for col, label in [("prix_median","prix"), ("prix_m2_median","prix_m2")]:
        v2020 = resultats[arr].get(f"{col}_2020")
        v2024 = resultats[arr].get(f"{col}_2024")
        if v2020 and v2024 and v2020 > 0:
            resultats[arr][f"evolution_{label}_2020_2024_pct"] = round((v2024-v2020)/v2020*100,1)
        else:
            resultats[arr][f"evolution_{label}_2020_2024_pct"] = None
    for i in range(len(ANNEES)-1):
        a1, a2 = ANNEES[i], ANNEES[i+1]
        for col, label in [("prix_median","prix"), ("prix_m2_median","prix_m2"), ("nb_ventes","volume")]:
            v1 = resultats[arr].get(f"{col}_{a1}")
            v2 = resultats[arr].get(f"{col}_{a2}")
            key = f"evolution_{label}_{a1}_{a2}_pct"
            if v1 and v2 and v1 > 0:
                resultats[arr][key] = round((v2-v1)/v1*100,1)
            else:
                resultats[arr][key] = None
    series_m2 = [resultats[arr].get(f"prix_m2_median_{a}") for a in ANNEES]
    series_m2 = [v for v in series_m2 if v]
    if len(series_m2) >= 3:
        evols = [(series_m2[i+1]-series_m2[i])/series_m2[i]*100 for i in range(len(series_m2)-1) if series_m2[i] > 0]
        moy = np.mean(evols)
        resultats[arr]["tendance_prix_m2"] = (
            "Forte hausse" if moy>5 else "Hausse modérée" if moy>2 else
            "Stable" if moy>-2 else "Baisse modérée" if moy>-5 else "Forte baisse"
        )
        resultats[arr]["evolution_annuelle_moyenne_pct"] = round(moy,1)
        resultats[arr]["volatilite_prix_m2"] = round(np.std(evols),1)

# ============================================================================
# ÉTAPE 6 : SYNTHÈSE LOGEMENTS 2024
# ============================================================================

print("\nÉTAPE 6 : Synthèse logements 2024...")

if 2024 in donnees_immo_par_annee:
    df_2024 = donnees_immo_par_annee[2024].copy()
    if "nature_mutation" in df_2024.columns:
        df_2024 = df_2024[df_2024["nature_mutation"] == "Vente"]
    for arr in range(1, 21):
        df_arr = df_2024[df_2024["arrondissement"] == arr].copy()
        if len(df_arr) == 0: continue
        if "type_local" in df_arr.columns:
            nb_ap = len(df_arr[df_arr["type_local"]=="Appartement"])
            nb_ma = len(df_arr[df_arr["type_local"]=="Maison"])
            tot = nb_ap + nb_ma
            resultats[arr]["nb_appartements_2024"] = nb_ap
            resultats[arr]["nb_maisons_2024"] = nb_ma
            resultats[arr]["pct_appartements"] = round(nb_ap/tot*100,1) if tot > 0 else None
        if "nombre_pieces_principales" in df_arr.columns:
            pieces = df_arr["nombre_pieces_principales"].dropna()
            pieces = pieces[(pieces > 0) & (pieces < 10)]
            resultats[arr]["nb_pieces_moyen"] = round(pieces.mean(),1) if len(pieces) > 0 else None

# ============================================================================
# ÉTAPE 7 : TRANSPORT
# ============================================================================

print("\nÉTAPE 7 : Transport...")

try:
    fichier_trafic = f"{BRONZE_PATH}\\trafic-annuel-entrant-par-station-du-reseau-ferre-2021.csv"
    df_transport = pd.read_csv(fichier_trafic, sep=";", low_memory=False)
    df_transport = df_transport.rename(columns={
        "Réseau":"reseau","Station":"station","Trafic":"trafic",
        "Correspondance_1":"corresp_1","Correspondance_2":"corresp_2",
        "Correspondance_3":"corresp_3","Correspondance_4":"corresp_4",
        "Correspondance_5":"corresp_5","Ville":"ville",
        "Arrondissement pour Paris":"arrondissement_paris",
    })
    df_transport = df_transport[df_transport["ville"] == "Paris"].copy()
    df_transport["arrondissement_paris"] = pd.to_numeric(df_transport["arrondissement_paris"], errors="coerce").astype("Int64")
    df_transport = df_transport[df_transport["arrondissement_paris"].between(1,20)].copy()
    df_transport["trafic"] = pd.to_numeric(df_transport["trafic"], errors="coerce").fillna(0).astype(int)
    corresp_cols = ["corresp_1","corresp_2","corresp_3","corresp_4","corresp_5"]
    for arr in range(1, 21):
        df_arr = df_transport[df_transport["arrondissement_paris"] == arr].copy()
        if len(df_arr) == 0: continue
        df_metro = df_arr[df_arr["reseau"] == "Métro"].copy()
        if len(df_metro) > 0:
            resultats[arr]["nb_stations_metro"] = int(len(df_metro))
            resultats[arr]["trafic_total_metro"] = int(df_metro["trafic"].sum())
            lignes = set()
            for col in corresp_cols:
                for v in df_metro[col].dropna().astype(str).str.strip():
                    if v and v.lower() != "nan": lignes.add(v)
            lignes = sorted(lignes, key=lambda x: (0,int(x)) if x.isdigit() else (1,x))
            resultats[arr]["nb_lignes_metro"] = len(lignes)
            resultats[arr]["lignes_metro"] = ", ".join(lignes)
        df_rer = df_arr[df_arr["reseau"].str.contains("RER", na=False)].copy()
        if len(df_rer) > 0:
            lignes_rer = set()
            for col in corresp_cols:
                for v in df_rer[col].dropna().astype(str).str.strip():
                    if v and v.lower() != "nan": lignes_rer.add(v)
            resultats[arr]["nb_lignes_rer"] = len(sorted(lignes_rer))
            resultats[arr]["lignes_rer"] = ", ".join(sorted(lignes_rer))
    print("  ✓ Transport chargé")
except Exception as e:
    print(f"  ⚠ Transport : {e}")

# ============================================================================
# ÉTAPE 8 : QUALITÉ DE L'AIR
# ============================================================================

print("\nÉTAPE 8 : Qualité de l'air...")

try:
    df_air = pd.read_csv(f"{SILVER_PATH}\\air_quality_paris_final.csv", sep=",", low_memory=False)
    df_air["arrondissement"] = df_air["arrondissement_nom"].apply(extraire_arrondissement_nom)
    for arr in range(1, 21):
        df_arr = df_air[df_air["arrondissement"] == arr].copy()
        if len(df_arr) == 0: continue
        for pol in ["no2","pm10","o3"]:
            if pol in df_arr.columns:
                resultats[arr][f"{pol}_moyen"] = round(df_arr[pol].mean(),1)
        if "qualite_air" in df_arr.columns:
            resultats[arr]["qualite_air_dominante"] = df_arr["qualite_air"].value_counts().index[0]
    print("  ✓ Qualité air chargée")
except Exception as e:
    print(f"  ⚠ Qualité air : {e}")

# ============================================================================
# ÉTAPE 9 : DÉMOGRAPHIE RÉELLE INSEE 2022 + REVENUS FiLoSoFi
# ============================================================================

print("\nÉTAPE 9 : Démographie réelle + revenus...")

# Charger les revenus depuis FiLoSoFi
revenus_par_arr = {}
try:
    df_filo = pd.read_excel(FICHIER_REVENUS, sheet_name="IRIS_DEC", header=5)
    df_filo["COM"] = df_filo["COM"].astype(str).str.zfill(5)
    paris_filo = df_filo[df_filo["COM"].str.startswith("751")].copy()
    paris_filo["arrondissement"] = paris_filo["COM"].str[-2:].astype(int)
    paris_filo["DEC_MED18"] = pd.to_numeric(paris_filo["DEC_MED18"], errors="coerce")
    revenus_par_arr = paris_filo.groupby("arrondissement")["DEC_MED18"].median().round(0).to_dict()
    print(f"  ✓ Revenus chargés pour {len(revenus_par_arr)} arrondissements")
except Exception as e:
    print(f"  ⚠ Revenus : {e}")

for arr in range(1, 21):
    # Vraies données démographiques INSEE 2022
    resultats[arr]["population_2022"]   = POPULATION_2022.get(arr)
    resultats[arr]["nb_menages_2022"]   = NB_MENAGES_2022.get(arr)
    resultats[arr]["nb_logements_2022"] = NB_LOGEMENTS_2022.get(arr)
    resultats[arr]["superficie_km2"]    = SUPERFICIE_KM2.get(arr)
    resultats[arr]["densite_pop_km2"]   = round(POPULATION_2022.get(arr,0) / SUPERFICIE_KM2.get(arr,1), 0)
    # Revenus médians réels
    resultats[arr]["revenu_median"] = int(revenus_par_arr[arr]) if arr in revenus_par_arr else None

# ============================================================================
# ÉTAPE 10 : LOGEMENTS SOCIAUX
# ============================================================================

print("\nÉTAPE 10 : Logements sociaux...")

for arr in range(1, 21):
    apur = LOGEMENTS_SOCIAUX_APUR.get(arr, {})
    resultats[arr]["nb_logements_sociaux_apur"]       = apur.get("nb")
    resultats[arr]["part_logements_sociaux_apur_pct"] = apur.get("pct")
    pct = apur.get("pct", 0)
    resultats[arr]["estimation_logement_social_pct"] = (
        "Élevé (>20%)" if pct > 20 else "Moyen (10-20%)" if pct >= 10 else "Faible (<10%)"
    )

# ============================================================================
# ÉTAPE 11 : CRÉATION DU DATAFRAME
# ============================================================================

print("\nÉTAPE 11 : Création du DataFrame final...")

df_final = pd.DataFrame.from_dict(resultats, orient="index").sort_values("Arrondissement")
print(f"  ✓ {len(df_final)} arrondissements × {len(df_final.columns)} colonnes")

# ============================================================================
# ÉTAPE 12 : 4 INDICATEURS COMPOSITES
# ============================================================================

print("\nÉTAPE 12 : Calcul des 4 indicateurs composites...")

def safe_norm(col, inverse=False):
    if col not in df_final.columns: return pd.Series([5.0]*len(df_final), index=df_final.index)
    s = pd.to_numeric(df_final[col], errors="coerce")
    s = s.fillna(s.median())
    return normaliser(s, inverse)

# 1. Accessibilité : nb d'années de revenu pour acheter 50m²
if "prix_m2_median_2024" in df_final.columns and "revenu_median" in df_final.columns:
    df_final["ratio_effort_achat"] = (
        pd.to_numeric(df_final["prix_m2_median_2024"], errors="coerce") * 50 /
        pd.to_numeric(df_final["revenu_median"], errors="coerce")
    ).round(2)
    df_final["indice_accessibilite"] = normaliser(df_final["ratio_effort_achat"], inverse=True).round(2)

# 2. Tension Sociale : prix élevé + peu de logements sociaux
df_final["indice_tension_sociale"] = (
    (safe_norm("prix_m2_median_2024") + safe_norm("part_logements_sociaux_apur_pct", inverse=True)) / 2
).round(2)

# 3. Attractivité : trafic métro + lignes + prix
df_final["indice_attractivite"] = (
    safe_norm("trafic_total_metro") * 0.4 +
    safe_norm("nb_lignes_metro") * 0.3 +
    safe_norm("prix_m2_median_2024") * 0.3
).round(2)

# 4. Pression Immobilière : baisse prix + fort volume + beaucoup de T1
df_final["indice_pression_immo"] = (
    safe_norm("evolution_prix_m2_2023_2024_pct", inverse=True) * 0.4 +
    safe_norm("nb_ventes_2024") * 0.3 +
    safe_norm("pct_T1_2024") * 0.3
).round(2)

print("  ✓ 4 indicateurs calculés")

# ============================================================================
# ÉTAPE 13 : SAUVEGARDE
# ============================================================================

print("\nÉTAPE 13 : Sauvegarde...")

import os
os.makedirs(os.path.dirname(FICHIER_SORTIE), exist_ok=True)
df_final.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig", sep=";")

print(f"\n{'='*80}")
print(f"✅ GOLD FINAL SAUVEGARDÉ → {FICHIER_SORTIE}")
print(f"   {len(df_final)} arrondissements × {len(df_final.columns)} colonnes")
print(f"\n   Colonnes clés présentes :")
cols_check = [
    "prix_m2_median_2024","nb_stations_metro","trafic_total_metro",
    "lignes_metro","no2_moyen","population_2022","revenu_median",
    "indice_accessibilite","indice_tension_sociale","indice_attractivite","indice_pression_immo"
]
for col in cols_check:
    status = "✓" if col in df_final.columns else "✗"
    print(f"   {status} {col}")
print(f"{'='*80}")