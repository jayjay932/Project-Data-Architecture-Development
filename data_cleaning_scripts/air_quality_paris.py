"""
Script de transformation des données QUALITÉ DE L'AIR
Objectif : Construire la ZONE SILVER à partir de la ZONE BRONZE

Input  : data/bronze/air_quality_paris.csv
Output : data/silver/air_quality_paris_silver.csv

Le script :
    ✔ nettoie les données
    ✔ corrige les codes INSEE
    ✔ ajoute les noms d’arrondissements
    ✔ supprime doublons et valeurs manquantes
    ✔ ajoute les catégories pollution
"""

import pandas as pd
from pathlib import Path

print("="*80)
print("TRANSFORMATION QUALITÉ DE L'AIR - ZONE SILVER")
print("="*80)
print()

# ============================================================================
# CHEMINS
# ============================================================================

DATA_DIR = Path("data")
BRONZE_FILE = DATA_DIR / "bronze" / "air_quality_paris.csv"
SILVER_DIR = DATA_DIR / "silver"
SILVER_FILE = SILVER_DIR / "air_quality_paris_silver.csv"

# Créer dossier silver si besoin
SILVER_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_arrondissement_name(ninsee: int) -> str:
    """
    Convertit un code INSEE en nom d'arrondissement.
    Ex : 75101 → "Paris 1er"
    """
    if pd.isna(ninsee) or ninsee == 0:
        return None

    arrondissement = int(str(ninsee)[-2:])
    suffix = "er" if arrondissement == 1 else "e"
    return f"Paris {arrondissement}{suffix}"


def categoriser_no2(val):
    if val < 40:
        return "Bonne"
    elif val < 50:
        return "Moyenne"
    else:
        return "Mauvaise"


def categoriser_pm10(val):
    if val < 20:
        return "Bonne"
    elif val < 40:
        return "Moyenne"
    else:
        return "Mauvaise"


def categoriser_o3(val):
    if val < 30:
        return "Bonne"
    elif val < 45:
        return "Moyenne"
    else:
        return "Mauvaise"


def qualite_globale(no2, pm10, o3):
    score = (no2 + pm10 + o3) / 3
    if score < 30:
        return "Bonne"
    elif score < 40:
        return "Moyenne"
    else:
        return "Mauvaise"


# ============================================================================
# ÉTAPE 1 : LECTURE BRONZE
# ============================================================================

print("Lecture des données Bronze...")
print("-"*80)

# On lit bien dans data/bronze/air_quality_paris.csv
df = pd.read_csv(BRONZE_FILE)

print(f"✓ Données chargées : {len(df)} lignes")
print(df.head())
print()

# ============================================================================
# ÉTAPE 2 : NETTOYAGE
# ============================================================================

print("Nettoyage des données...")
print("-"*80)

# Supprimer doublons
df = df.drop_duplicates()

# Supprimer valeurs manquantes
df = df.dropna()

# Conversion date (format JJ/MM/AAAA dans ton exemple)
df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

# Conversion numérique (au cas où)
for col in ["no2", "pm10", "o3", "ninsee"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Supprimer les lignes sans code INSEE utilisable
df = df[df["ninsee"].notna()]

# Correction des codes INSEE courts → mapping vers codes complets
mapping_insee = {
    75: 75101,
    77: 75102,
    78: 75103,
    # 79: 75104,  # à activer si tu as ce cas
}

df["ninsee"] = df["ninsee"].replace(mapping_insee)

# Filtrer les codes INSEE invalides (on garde que Paris 75xxx)
# Garder UNIQUEMENT les 20 arrondissements de Paris
df = df[(df["ninsee"] >= 75101) & (df["ninsee"] <= 75120)]


print(f"✓ Données nettoyées : {len(df)} lignes")
print()

# ============================================================================
# ÉTAPE 3 : AJOUT ARRONDISSEMENT & CATÉGORIES
# ============================================================================

print("Ajout des colonnes Silver...")
print("-"*80)

df["arrondissement_nom"] = df["ninsee"].apply(get_arrondissement_name)

df["categorie_no2"] = df["no2"].apply(categoriser_no2)
df["categorie_pm10"] = df["pm10"].apply(categoriser_pm10)
df["categorie_o3"] = df["o3"].apply(categoriser_o3)

df["qualite_air"] = df.apply(
    lambda row: qualite_globale(row["no2"], row["pm10"], row["o3"]),
    axis=1
)

print("✓ Colonnes ajoutées : arrondissement_nom, catégories, qualite_air")
print()

# ============================================================================
# ÉTAPE 4 : SAUVEGARDE SILVER
# ============================================================================

print("Sauvegarde de la zone Silver...")
print("-"*80)

df.to_csv(SILVER_FILE, index=False, sep=";")

print(f"✓ Fichier Silver généré : {SILVER_FILE}")
print()
print("="*80)
print("✔ TRANSFORMATION SILVER TERMINÉE AVEC SUCCÈS")
print("="*80)
