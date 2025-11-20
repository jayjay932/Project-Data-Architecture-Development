"""
Script d'agrégation complète des données par arrondissement de Paris
Produit UN SEUL CSV : dashboard_arrondissements_paris3.csv

Métriques incluses :
- Prix/m² médian et évolution temporelle
- Valeur médiane des ventes
- Typologie des logements (types + nombre de pièces)
- Part de logements sociaux (APUR + estimation)
- Transport (stations, lignes métro / RER, trafic)
- Qualité de l'air (pollution)
- Statistiques démographiques
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
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

SILVER_PATH = r"C:\Users\jason\Downloads\projet_data_architecture\data\silver"
BRONZE_PATH = r"C:\Users\jason\Downloads\projet_data_architecture\data\bronze"
FICHIER_SORTIE = "dashboard_arrondissements_paris7.csv"

ANNEES = [2020, 2021, 2022, 2023, 2024, 2025]

print(f"📂 Répertoire Silver : {SILVER_PATH}")
print(f"📂 Répertoire Bronze : {BRONZE_PATH}")
print(f"📊 Années : {ANNEES}")
print(f"💾 Sortie : {FICHIER_SORTIE}")
print()

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def extraire_arrondissement(code_postal):
    """Extrait l'arrondissement depuis code postal (75001-75020)"""
    if pd.isna(code_postal):
        return None
    code = str(int(code_postal)) if isinstance(code_postal, float) else str(code_postal)
    if code.startswith('75') and len(code) == 5:
        arr = int(code[-2:])
        return arr if 1 <= arr <= 20 else None
    return None


def extraire_arrondissement_nom(nom):
    """Extrait arrondissement depuis 'Paris 8e Arrondissement'"""
    if pd.isna(nom):
        return None
    match = re.search(r'(\d+)[eér]', str(nom))
    if match:
        arr = int(match.group(1))
        return arr if 1 <= arr <= 20 else None
    return None


def extraire_arrondissement_insee(code):
    """Extrait arrondissement depuis code INSEE (75101-75120)"""
    if pd.isna(code):
        return None
    code = str(int(code)) if isinstance(code, float) else str(code)
    if code.startswith('751') and len(code) == 5:
        arr = int(code[-2:])
        return arr if 1 <= arr <= 20 else None
    return None


def piece_to_typologie(n):
    """Convertit nombre de pièces en T1/T2/T3/T4/T5plus"""
    if pd.isna(n):
        return None
    try:
        n = int(n)
    except Exception:
        return None
    if n <= 0:
        return None
    if n == 1:
        return "T1"
    if n == 2:
        return "T2"
    if n == 3:
        return "T3"
    if n == 4:
        return "T4"
    return "T5plus"


# ============================================================================
# ÉTAPE 1 : DONNÉES IMMOBILIÈRES (2020-2025)
# ============================================================================

print("ÉTAPE 1 : Chargement des données immobilières...")
print("-" * 100)

donnees_immo_par_annee = {}

for annee in ANNEES:
    fichier_clean = f"{SILVER_PATH}\\75_{annee}_clean.csv"
    fichier_lots = f"{SILVER_PATH}\\75_{annee}_lots.csv"

    try:
        df_clean = pd.read_csv(fichier_clean, sep=",", low_memory=False)
        print(f"  ✓ {annee} clean : {len(df_clean)} lignes")

        # Extraire arrondissement
        if "arrondissement" not in df_clean.columns:
            if "code_postal" in df_clean.columns:
                df_clean["arrondissement"] = df_clean["code_postal"].apply(extraire_arrondissement)
            elif "nom_commune" in df_clean.columns:
                df_clean["arrondissement"] = df_clean["nom_commune"].apply(extraire_arrondissement_nom)

        # Filtrer arrondissements valides
        df_clean = df_clean[df_clean["arrondissement"].notna()].copy()
        df_clean["arrondissement"] = df_clean["arrondissement"].astype(int)

        # Joindre les lots pour surface_carrez si dispo
        try:
            df_lots = pd.read_csv(fichier_lots, sep=",", low_memory=False)
            if "id_mutation" in df_clean.columns and "id_mutation" in df_lots.columns:
                df_clean = df_clean.merge(
                    df_lots[["id_mutation", "surface_carrez"]].drop_duplicates(),
                    on="id_mutation",
                    how="left",
                )
        except Exception:
            pass

        donnees_immo_par_annee[annee] = df_clean

    except Exception as e:
        print(f"  ⚠ {annee} : Fichier non trouvé ou erreur - {e}")

print()

# ============================================================================
# ÉTAPE 2 : AGRÉGATION IMMOBILIÈRE PAR ARRONDISSEMENT
# ============================================================================

print("ÉTAPE 2 : Agrégation des données immobilières...")
print("-" * 100)

resultats = {}

for arr in range(1, 21):
    resultats[arr] = {"Arrondissement": arr}

for annee in ANNEES:
    if annee not in donnees_immo_par_annee:
        continue

    df = donnees_immo_par_annee[annee].copy()
    print(f"\n  [{annee}] Agrégation...")

    for arr in range(1, 21):
        df_arr = df[df["arrondissement"] == arr].copy()

        if len(df_arr) == 0:
            resultats[arr][f"nb_ventes_{annee}"] = 0
            resultats[arr][f"prix_median_{annee}"] = None
            resultats[arr][f"prix_m2_median_{annee}"] = None
            continue

        # Filtrer uniquement les ventes
        if "nature_mutation" in df_arr.columns:
            df_arr = df_arr[df_arr["nature_mutation"] == "Vente"]

        # Appartements pour calcul du prix/m²
        if "type_local" in df_arr.columns:
            df_appart = df_arr[df_arr["type_local"] == "Appartement"].copy()
        else:
            df_appart = df_arr.copy()

        # Nombre de ventes
        resultats[arr][f"nb_ventes_{annee}"] = len(df_arr)

        # Prix médian
        if "valeur_fonciere" in df_arr.columns:
            prix_valides = df_arr["valeur_fonciere"].dropna()
            prix_valides = prix_valides[(prix_valides > 10000) & (prix_valides < 10000000)]
            resultats[arr][f"prix_median_{annee}"] = int(prix_valides.median()) if len(prix_valides) > 0 else None

        # Prix/m² médian
        prix_m2_list = []
        for _, row in df_appart.iterrows():
            vf = row.get("valeur_fonciere")
            sr = row.get("surface_reelle_bati")
            sc = row.get("surface_carrez")
            if pd.notna(vf):
                surface = None
                if pd.notna(sr) and sr > 0:
                    surface = sr
                elif pd.notna(sc) and sc > 0:
                    surface = sc
                if surface:
                    prix_m2 = vf / surface
                    if 3000 < prix_m2 < 50000:
                        prix_m2_list.append(prix_m2)

        resultats[arr][f"prix_m2_median_{annee}"] = int(np.median(prix_m2_list)) if prix_m2_list else None

        print(
            f"    Arr. {arr:2d} : {len(df_arr):4d} ventes, "
            f"Prix: {resultats[arr][f'prix_median_{annee}'] or 0:>9,}€, "
            f"Prix/m²: {resultats[arr][f'prix_m2_median_{annee}'] or 0:>6,}€/m²"
        )

print()

# ============================================================================
# ÉTAPE 3 : ANALYSE DES TYPES DE LOCAUX (par année, par arrondissement)
# ============================================================================

print("ÉTAPE 3 : Analyse des types de locaux...")
print("-" * 100)

for annee in ANNEES:
    if annee not in donnees_immo_par_annee:
        continue

    print(f"  Année {annee}...")

    df_annee = donnees_immo_par_annee[annee].copy()

    # Filtrer Paris + ventes uniquement
    if "code_departement" in df_annee.columns:
        df_annee = df_annee[df_annee["code_departement"] == "75"].copy()

    if "nature_mutation" in df_annee.columns:
        df_annee = df_annee[df_annee["nature_mutation"] == "Vente"].copy()

    if "arrondissement" not in df_annee.columns and "code_commune" in df_annee.columns:
        df_annee["arrondissement"] = df_annee["code_commune"].astype(str).str[-2:].astype(int)

    for arr in range(1, 21):
        df_arr = df_annee[df_annee["arrondissement"] == arr].copy()

        if len(df_arr) == 0 or "type_local" not in df_arr.columns:
            continue

        type_counts = df_arr["type_local"].value_counts()
        total_ventes = len(df_arr)

        # Répartition par type_local (nb + %)
        for type_local, count in type_counts.items():
            if pd.isna(type_local):
                continue
            if type_local == "Appartement":
                type_clean = "appartement"
            elif type_local == "Maison":
                type_clean = "maison"
            elif type_local.startswith("Local industriel"):
                type_clean = "local_industriel_commercial_ou_assimilé"
            elif type_local == "Dépendance":
                type_clean = "dépendance"
            else:
                # On peut stocker d'autres types si besoin
                type_clean = type_local.lower().replace(" ", "_").replace("/", "_").replace(",", "").replace(".", "")

            pct = (count / total_ventes) * 100 if total_ventes > 0 else 0.0
            resultats[arr][f"nb_{type_clean}_{annee}"] = int(count)
            resultats[arr][f"pct_{type_clean}_{annee}"] = round(pct, 1)

        # Type dominant
        if len(type_counts) > 0:
            resultats[arr][f"type_dominant_{annee}"] = type_counts.index[0]

        # Prix médian + prix/m2 médian par type principal
        for type_local in df_arr["type_local"].dropna().unique():
            if type_local == "Appartement":
                type_clean = "appartement"
            elif type_local == "Maison":
                type_clean = "maison"
            elif type_local.startswith("Local industriel"):
                type_clean = "local_industriel_commercial_ou_assimilé"
            elif type_local == "Dépendance":
                type_clean = "dépendance"
            else:
                type_clean = type_local.lower().replace(" ", "_").replace("/", "_").replace(",", "").replace(".", "")

            df_type = df_arr[df_arr["type_local"] == type_local].copy()
            if len(df_type) < 3:
                continue

            # Prix médian
            if "valeur_fonciere" in df_type.columns:
                prix_valides = df_type["valeur_fonciere"].dropna()
                prix_valides = prix_valides[(prix_valides > 10000) & (prix_valides < 20000000)]
                if len(prix_valides) > 0:
                    resultats[arr][f"prix_median_{type_clean}_{annee}"] = int(prix_valides.median())

            # Prix/m² médian (appartement / maison)
            if type_local in ["Appartement", "Maison"]:
                prix_m2_list = []
                for _, row in df_type.iterrows():
                    vf = row.get("valeur_fonciere")
                    sr = row.get("surface_reelle_bati")
                    if pd.notna(vf) and pd.notna(sr) and sr > 0:
                        prix_m2 = vf / sr
                        if 1000 < prix_m2 < 100000:
                            prix_m2_list.append(prix_m2)
                if prix_m2_list:
                    resultats[arr][f"prix_m2_median_{type_clean}_{annee}"] = int(np.median(prix_m2_list))

print("  ✓ Analyse des types de locaux terminée")
print()

# ============================================================================
# ÉTAPE 4 : TYPOLOGIE PAR NOMBRE DE PIÈCES (T1, T2, T3, T4, T5+)
# ============================================================================

print("ÉTAPE 4 : Typologie par nombre de pièces (T1, T2, T3, T4, T5+)...")
print("-" * 100)

for annee in ANNEES:
    if annee not in donnees_immo_par_annee:
        continue

    df_typo = donnees_immo_par_annee[annee].copy()
    if "nombre_pieces_principales" not in df_typo.columns:
        continue

    # On se limite aux logements résidentiels classiques
    if "type_local" in df_typo.columns:
        df_typo = df_typo[df_typo["type_local"].isin(["Appartement", "Maison"])].copy()

    df_typo["typologie"] = df_typo["nombre_pieces_principales"].apply(piece_to_typologie)

    for arr in range(1, 21):
        df_arr = df_typo[df_typo["arrondissement"] == arr].copy()
        if len(df_arr) == 0:
            continue

        total = len(df_arr)
        counts = df_arr["typologie"].value_counts()

        for t in ["T1", "T2", "T3", "T4", "T5plus"]:
            nb = int(counts.get(t, 0))
            pct = round((nb / total) * 100, 1) if total > 0 else 0.0
            resultats[arr][f"nb_{t}_{annee}"] = nb
            resultats[arr][f"pct_{t}_{annee}"] = pct

        # Comptage des maisons (tous types de pièces) par année
        if "type_local" in df_arr.columns:
            nb_maison = len(df_arr[df_arr["type_local"] == "Maison"])
            pct_maison = round((nb_maison / total) * 100, 1) if total > 0 else 0.0
            resultats[arr][f"nb_maison_{annee}"] = nb_maison
            resultats[arr][f"pct_maison_{annee}"] = pct_maison

print("  ✓ Typologie par pièces calculée")
print()

# ============================================================================
# ÉTAPE 5 : ÉVOLUTION TEMPORELLE DÉTAILLÉE
# ============================================================================

print("ÉTAPE 5 : Calcul des évolutions temporelles...")
print("-" * 100)

for arr in range(1, 21):
    # 5.1 Évolution globale 2020–2024
    prix_2020 = resultats[arr].get("prix_median_2020")
    prix_2024 = resultats[arr].get("prix_median_2024")

    if prix_2020 and prix_2024 and prix_2020 > 0:
        evolution_pct = ((prix_2024 - prix_2020) / prix_2020) * 100
        resultats[arr]["evolution_prix_2020_2024_pct"] = round(evolution_pct, 1)
    else:
        resultats[arr]["evolution_prix_2020_2024_pct"] = None

    prixm2_2020 = resultats[arr].get("prix_m2_median_2020")
    prixm2_2024 = resultats[arr].get("prix_m2_median_2024")

    if prixm2_2020 and prixm2_2024 and prixm2_2020 > 0:
        evolution_pct = ((prixm2_2024 - prixm2_2020) / prixm2_2020) * 100
        resultats[arr]["evolution_prix_m2_2020_2024_pct"] = round(evolution_pct, 1)
    else:
        resultats[arr]["evolution_prix_m2_2020_2024_pct"] = None

    # 5.2 évolutions année par année (prix médian)
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]

        prix_actuel = resultats[arr].get(f"prix_median_{annee_actuelle}")
        prix_suivant = resultats[arr].get(f"prix_median_{annee_suivante}")

        if prix_actuel and prix_suivant and prix_actuel > 0:
            evolution_annuelle = ((prix_suivant - prix_actuel) / prix_actuel) * 100
            resultats[arr][f"evolution_prix_{annee_actuelle}_{annee_suivante}_pct"] = round(evolution_annuelle, 1)
        else:
            resultats[arr][f"evolution_prix_{annee_actuelle}_{annee_suivante}_pct"] = None

    # 5.3 évolutions année par année (prix/m²)
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]

        prixm2_actuel = resultats[arr].get(f"prix_m2_median_{annee_actuelle}")
        prixm2_suivant = resultats[arr].get(f"prix_m2_median_{annee_suivante}")

        if prixm2_actuel and prixm2_suivant and prixm2_actuel > 0:
            evolution_annuelle = ((prixm2_suivant - prixm2_actuel) / prixm2_actuel) * 100
            resultats[arr][f"evolution_prix_m2_{annee_actuelle}_{annee_suivante}_pct"] = round(evolution_annuelle, 1)
        else:
            resultats[arr][f"evolution_prix_m2_{annee_actuelle}_{annee_suivante}_pct"] = None

    # 5.4 tendance générale & volatilité (prix/m²)
    prix_m2_series = []
    for annee in ANNEES:
        val = resultats[arr].get(f"prix_m2_median_{annee}")
        if val:
            prix_m2_series.append(val)

    if len(prix_m2_series) >= 3:
        evolutions = []
        for i in range(len(prix_m2_series) - 1):
            if prix_m2_series[i] > 0:
                evol = ((prix_m2_series[i + 1] - prix_m2_series[i]) / prix_m2_series[i]) * 100
                evolutions.append(evol)

        if evolutions:
            moyenne_evolution = np.mean(evolutions)
            if moyenne_evolution > 5:
                tendance = "Forte hausse"
            elif moyenne_evolution > 2:
                tendance = "Hausse modérée"
            elif moyenne_evolution > -2:
                tendance = "Stable"
            elif moyenne_evolution > -5:
                tendance = "Baisse modérée"
            else:
                tendance = "Forte baisse"

            resultats[arr]["tendance_prix_m2"] = tendance
            resultats[arr]["evolution_annuelle_moyenne_pct"] = round(moyenne_evolution, 1)
            resultats[arr]["volatilite_prix_m2"] = round(np.std(evolutions), 1) if len(evolutions) > 1 else None
        else:
            resultats[arr]["tendance_prix_m2"] = "Données insuffisantes"
            resultats[arr]["evolution_annuelle_moyenne_pct"] = None
            resultats[arr]["volatilite_prix_m2"] = None
    else:
        resultats[arr]["tendance_prix_m2"] = "Données insuffisantes"
        resultats[arr]["evolution_annuelle_moyenne_pct"] = None
        resultats[arr]["volatilite_prix_m2"] = None

    # 5.5 évolution volume de ventes
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]

        nb_ventes_actuel = resultats[arr].get(f"nb_ventes_{annee_actuelle}")
        nb_ventes_suivant = resultats[arr].get(f"nb_ventes_{annee_suivante}")

        if nb_ventes_actuel and nb_ventes_suivant and nb_ventes_actuel > 0:
            evolution_volume = ((nb_ventes_suivant - nb_ventes_actuel) / nb_ventes_actuel) * 100
            resultats[arr][f"evolution_volume_{annee_actuelle}_{annee_suivante}_pct"] = round(evolution_volume, 1)
        else:
            resultats[arr][f"evolution_volume_{annee_actuelle}_{annee_suivante}_pct"] = None

print("  ✓ Évolutions temporelles détaillées calculées")
print()

# ============================================================================
# ÉTAPE 6 : TYPOLOGIE SIMPLIFIÉE (Appart / Maison, nb pièces moyen – 2024)
# ============================================================================

print("ÉTAPE 6 : Typologie simplifiée (Appart/Maison, nb pièces moyen)...")
print("-" * 100)

if 2024 in donnees_immo_par_annee:
    df_2024 = donnees_immo_par_annee[2024].copy()

    for arr in range(1, 21):
        df_arr = df_2024[df_2024["arrondissement"] == arr].copy()

        if len(df_arr) == 0:
            continue

        if "type_local" in df_arr.columns:
            nb_appart = len(df_arr[df_arr["type_local"] == "Appartement"])
            nb_maison = len(df_arr[df_arr["type_local"] == "Maison"])
            total_mais_app = nb_appart + nb_maison

            resultats[arr]["nb_appartements_2024"] = nb_appart
            resultats[arr]["nb_maisons_2024"] = nb_maison
            resultats[arr]["pct_appartements"] = (
                round((nb_appart / total_mais_app) * 100, 1) if total_mais_app > 0 else None
            )

        if "nombre_pieces_principales" in df_arr.columns:
            pieces = df_arr["nombre_pieces_principales"].dropna()
            pieces = pieces[(pieces > 0) & (pieces < 10)]
            resultats[arr]["nb_pieces_moyen"] = round(pieces.mean(), 1) if len(pieces) > 0 else None

print("  ✓ Typologie simplifiée analysée")
print()

# ============================================================================
# ÉTAPE 7 : DONNÉES TRANSPORT (Bronze -> agrégation par arrondissement)
# ============================================================================

print("ÉTAPE 7 : Chargement des données transport (stations métro / RER)...")
print("-" * 100)

try:
    fichier_trafic = f"{BRONZE_PATH}\\trafic-annuel-entrant-par-station-du-reseau-ferre-2021.csv"
    df_transport = pd.read_csv(fichier_trafic, sep=";", low_memory=False)
    print(f"  ✓ Transport brut chargé : {len(df_transport)} lignes")

    df_transport = df_transport.rename(
        columns={
            "Réseau": "reseau",
            "Station": "station",
            "Trafic": "trafic",
            "Correspondance_1": "corresp_1",
            "Correspondance_2": "corresp_2",
            "Correspondance_3": "corresp_3",
            "Correspondance_4": "corresp_4",
            "Correspondance_5": "corresp_5",
            "Ville": "ville",
            "Arrondissement pour Paris": "arrondissement_paris",
        }
    )

    df_transport = df_transport[df_transport["ville"] == "Paris"].copy()
    df_transport["arrondissement_paris"] = pd.to_numeric(
        df_transport["arrondissement_paris"], errors="coerce"
    ).astype("Int64")
    df_transport = df_transport[
        df_transport["arrondissement_paris"].between(1, 20)
    ].copy()

    df_transport["trafic"] = pd.to_numeric(df_transport["trafic"], errors="coerce").fillna(0).astype(int)
    corresp_cols = ["corresp_1", "corresp_2", "corresp_3", "corresp_4", "corresp_5"]

    for arr in range(1, 21):
        df_arr = df_transport[df_transport["arrondissement_paris"] == arr].copy()
        if len(df_arr) == 0:
            continue

        # Métro
        df_metro = df_arr[df_arr["reseau"] == "Métro"].copy()
        if len(df_metro) > 0:
            resultats[arr]["nb_stations_metro"] = int(len(df_metro))
            resultats[arr]["trafic_total_metro"] = int(df_metro["trafic"].sum())

            lignes_metro = set()
            for col in corresp_cols:
                valeurs = df_metro[col].dropna().astype(str).str.strip()
                for v in valeurs:
                    if v and v.lower() != "nan":
                        lignes_metro.add(v)

            def key_metro(x: str):
                x = x.strip()
                if x.isdigit():
                    return (0, int(x))
                return (1, x)

            lignes_metro = sorted(lignes_metro, key=key_metro)
            resultats[arr]["nb_lignes_metro"] = len(lignes_metro)
            resultats[arr]["lignes_metro"] = ", ".join(lignes_metro)

        # RER
        df_rer = df_arr[df_arr["reseau"].str.contains("RER", na=False)].copy()
        if len(df_rer) > 0:
            lignes_rer = set()
            for col in corresp_cols:
                valeurs = df_rer[col].dropna().astype(str).str.strip()
                for v in valeurs:
                    if v and v.lower() != "nan":
                        lignes_rer.add(v)

            lignes_rer = sorted(lignes_rer)
            resultats[arr]["nb_lignes_rer"] = len(lignes_rer)
            resultats[arr]["lignes_rer"] = ", ".join(lignes_rer)

    print("  ✓ Données transport détaillées intégrées (stations -> arrondissements)")
except Exception as e:
    print(f"  ⚠ Erreur transport : {e}")

print()

# ============================================================================
# ÉTAPE 8 : QUALITÉ DE L'AIR
# ============================================================================

print("ÉTAPE 8 : Chargement des données qualité de l'air...")
print("-" * 100)

try:
    df_air = pd.read_csv(f"{SILVER_PATH}\\air_quality_paris_final.csv", sep=",", low_memory=False)
    print(f"  ✓ Qualité air chargée : {len(df_air)} lignes")

    df_air["arrondissement"] = df_air["arrondissement_nom"].apply(extraire_arrondissement_nom)

    for arr in range(1, 21):
        df_arr = df_air[df_air["arrondissement"] == arr].copy()
        if len(df_arr) == 0:
            continue

        if "no2" in df_arr.columns:
            resultats[arr]["no2_moyen"] = round(df_arr["no2"].mean(), 1)
        if "pm10" in df_arr.columns:
            resultats[arr]["pm10_moyen"] = round(df_arr["pm10"].mean(), 1)
        if "o3" in df_arr.columns:
            resultats[arr]["o3_moyen"] = round(df_arr["o3"].mean(), 1)

        if "qualite_air" in df_arr.columns:
            qual_counts = df_arr["qualite_air"].value_counts()
            if len(qual_counts) > 0:
                resultats[arr]["qualite_air_dominante"] = qual_counts.index[0]

    print("  ✓ Données qualité air intégrées")
except Exception as e:
    print(f"  ⚠ Erreur qualité air : {e}")

print()

# ============================================================================
# ÉTAPE 9 : STATISTIQUES COMMUNES
# ============================================================================

print("ÉTAPE 9 : Chargement des statistiques communes...")
print("-" * 100)

try:
    df_stats = pd.read_csv(f"{SILVER_PATH}\\stats_commune_2014_2020.csv", sep=",", low_memory=False)
    print(f"  ✓ Stats communes chargées : {len(df_stats)} lignes")

    df_stats_2020 = df_stats[df_stats["anneemut"] == 2020].copy()

    if "codgeo_2020" in df_stats_2020.columns:
        df_stats_2020["arrondissement"] = df_stats_2020["codgeo_2020"].apply(extraire_arrondissement_insee)
    elif "nom_commune" in df_stats_2020.columns:
        df_stats_2020["arrondissement"] = df_stats_2020["nom_commune"].apply(extraire_arrondissement_nom)

    for arr in range(1, 21):
        df_arr = df_stats_2020[df_stats_2020["arrondissement"] == arr].copy()
        if len(df_arr) == 0:
            continue

        row = df_arr.iloc[0]

        pop = row.get("POP_2018")
        menages = row.get("Nbre-menages_2018")
        logts = row.get("Logement_2018")
        prix_stats = row.get("vfm2_ventea")

        resultats[arr]["population_2018"] = int(pop) if pd.notna(pop) else None
        resultats[arr]["nb_menages_2018"] = int(menages) if pd.notna(menages) else None
        resultats[arr]["nb_logements_2018"] = int(logts) if pd.notna(logts) else None
        resultats[arr]["prix_m2_stats_2020"] = int(prix_stats) if pd.notna(prix_stats) else None

    print("  ✓ Statistiques communes intégrées")
except Exception as e:
    print(f"  ⚠ Erreur stats communes : {e}")

print()

# ============================================================================
# ÉTAPE 10 : LOGEMENTS SOCIAUX (APUR + estimation)
# ============================================================================

print("ÉTAPE 10 : Intégration des logements sociaux (APUR + estimation)...")
print("-" * 100)

# ⚠ IMPORTANT :
# Complète ce dictionnaire avec les valeurs APUR exactes (nb + %)
# pour chaque arrondissement 1..20.
logements_sociaux_apur = {
    1:  {"nb": 1307,  "pct": 12.5},
    2:  {"nb": 893,   "pct": 6.7},
    3:  {"nb": 1838,  "pct": 9.0},
    4:  {"nb": 2553,  "pct": 14.9},
    5:  {"nb": 3267,  "pct": 9.9},
    6:  {"nb": 959,   "pct": 3.7},
    7:  {"nb": 904,   "pct": 2.7},
    8:  {"nb": 955,   "pct": 3.9},
    9:  {"nb": 2660,  "pct": 7.4},
    10: {"nb": 8543,  "pct": 17.2},
    11: {"nb": 13176, "pct": 15.5},
    12: {"nb": 20177, "pct": 27.4},
    13: {"nb": 39162, "pct": 43.8},
    14: {"nb": 22500, "pct": 30.9},
    15: {"nb": 26183, "pct": 20.6},
    16: {"nb": 6304,  "pct": 6.6},
    17: {"nb": 16711, "pct": 17.6},
    18: {"nb": 25697, "pct": 25.3},
    19: {"nb": 38390, "pct": 46.0},
    20: {"nb": 39727, "pct": 43.6},
}

for arr in range(1, 21):
    apur = logements_sociaux_apur.get(arr)
    if apur:
        resultats[arr]["nb_logements_sociaux_apur"] = int(apur["nb"])
        resultats[arr]["part_logements_sociaux_apur_pct"] = float(apur["pct"])
    else:
        resultats[arr]["nb_logements_sociaux_apur"] = None
        resultats[arr]["part_logements_sociaux_apur_pct"] = None

# Estimation "basée prix/m²"
prix_m2_paris = [
    resultats[arr].get("prix_m2_median_2024")
    for arr in range(1, 21)
    if resultats[arr].get("prix_m2_median_2024")
]

if prix_m2_paris:
    mediane_paris = np.median(prix_m2_paris)
    for arr in range(1, 21):
        prix_arr = resultats[arr].get("prix_m2_median_2024")
        if prix_arr:
            if prix_arr < mediane_paris * 0.7:
                resultats[arr]["estimation_logement_social_pct"] = "Élevé (>20%)"
            elif prix_arr < mediane_paris * 0.85:
                resultats[arr]["estimation_logement_social_pct"] = "Moyen (10-20%)"
            else:
                resultats[arr]["estimation_logement_social_pct"] = "Faible (<10%)"
        else:
            resultats[arr]["estimation_logement_social_pct"] = "Non estimé"

print("  ✓ Logements sociaux intégrés (APUR + estimation)")
print()

# ============================================================================
# ÉTAPE 11 : CRÉATION DU DATAFRAME FINAL
# ============================================================================

print("ÉTAPE 11 : Création du DataFrame final...")
print("-" * 100)

df_final = pd.DataFrame.from_dict(resultats, orient="index")
df_final = df_final.sort_values("Arrondissement")

print(f"  ✓ DataFrame créé : {len(df_final)} arrondissements × {len(df_final.columns)} colonnes")
print()

# ============================================================================
# ÉTAPE 12 : SAUVEGARDE
# ============================================================================

print("ÉTAPE 12 : Sauvegarde du fichier CSV...")
print("-" * 100)

df_final.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig", sep=";")
print(f"  ✓ Fichier sauvegardé : {FICHIER_SORTIE}")
print()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("=" * 100)
print("RÉSUMÉ FINAL")
print("=" * 100)
print()

print(f"📊 DASHBOARD CRÉÉ : {FICHIER_SORTIE}")
print(f"   • {len(df_final)} arrondissements")
print(f"   • {len(df_final.columns)} colonnes de données")
print()

print("📈 MÉTRIQUES INCLUSES :")
print()
print("  1️⃣ IMMOBILIER (2020-2025)")
print("     • Nombre de ventes par an")
print("     • Prix médian par an")
print("     • Prix/m² médian par an")
print("     • Évolution 2020-2024 (prix et prix/m²)")
print()
print("  2️⃣ TYPOLOGIE DES LOGEMENTS")
print("     • Répartition par type_local (appartement / maison / etc.)")
print("     • Typologie par nombre de pièces (T1, T2, T3, T4, T5+)")
print("     • Nombre moyen de pièces")
print()
print("  3️⃣ LOGEMENTS SOCIAUX")
print("     • Nombre et % (APUR) par arrondissement")
print("     • Estimation qualitative (élevé / moyen / faible)")
print()
print("  4️⃣ TRANSPORT")
print("     • Nombre de stations de métro")
print("     • Trafic total métro")
print("     • Nombre et liste des lignes de métro et de RER")
print()
print("  5️⃣ QUALITÉ DE L'AIR")
print("     • NO2 / PM10 / O3 moyens")
print("     • Qualité de l'air dominante")
print()
print("  6️⃣ DÉMOGRAPHIE")
print("     • Population, ménages, logements (2018)")
print("     • Prix/m² INSEE (vfm2_ventea 2020)")
print()

print("🏆 TOP 5 ARRONDISSEMENTS (prix/m² 2024) :")
print()

if "prix_m2_median_2024" in df_final.columns:
    top5_prix = df_final.nlargest(5, "prix_m2_median_2024")
    for _, row in top5_prix.iterrows():
        if pd.notna(row["prix_m2_median_2024"]):
            print(f"    {int(row['Arrondissement']):2d}e : {int(row['prix_m2_median_2024']):>6,}€/m²")
    print()

print("=" * 100)
print("✅ DASHBOARD CRÉÉ AVEC SUCCÈS !")
print("=" * 100)
print()

print(f"💾 Fichier disponible : {FICHIER_SORTIE}")
print()
