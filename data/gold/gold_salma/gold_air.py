"""
Script de transformation des données de qualité de l'air à Paris
Objectif : Construire la zone GOLD à partir de la zone SILVER

Input  : air_quality_paris_silver.csv
         (colonnes attendues :
            date, arrondissement_nom, ninsee, no2, o3, pm10,
            qualite_air, categorie_no2, categorie_pm10, categorie_o3)

Output : air_quality_paris_gold_annual.csv   (agrégation annuelle par arrondissement)
         air_quality_paris_gold_monthly.csv  (agrégation mensuelle par arrondissement - optionnel)
"""

from pathlib import Path
import pandas as pd

print("=" * 80)
print("TRANSFORMATION DONNÉES QUALITÉ DE L'AIR - CONSTRUCTION ZONE GOLD")
print("=" * 80)
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

# On part du dossier du projet (là où tu lances python)
# Exemple : C:\Users\dissi\Project-Data-Architecture-Development
DATA_DIR = Path("data")

# Fichier d'entrée : ton Silver généré juste avant
FICHIER_ENTREE = DATA_DIR / "silver" / "air_quality_paris_silver.csv"

# Dossier de sortie pour ta zone Gold perso
GOLD_DIR = DATA_DIR / "gold" / "gold_salma"
GOLD_DIR.mkdir(parents=True, exist_ok=True)

# Fichiers de sortie (zone GOLD)
FICHIER_SORTIE_ANNUEL = GOLD_DIR / "air_quality_paris_gold_annual.csv"
FICHIER_SORTIE_MENSUEL = GOLD_DIR / "air_quality_paris_gold_monthly.csv"

print(f" Fichier d'entrée  : {FICHIER_ENTREE}")
print(f" Fichier sortie AN : {FICHIER_SORTIE_ANNUEL}")
print(f" Fichier sortie MO : {FICHIER_SORTIE_MENSUEL}")
print()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_mode_or_nan(series: pd.Series):
    """Retourne la modalité la plus fréquente d'une série (ex: 'Bonne', 'Moyenne', etc.)."""
    mode = series.mode()
    if mode.empty:
        return pd.NA
    return mode.iat[0]


def categoriser_indice_global(val: float) -> str:
    """
    Catégorise l'indice global de pollution en classes qualitatives.
    Seuils à adapter si besoin.

        < 20   → 'Bonne'
        20-35  → 'Moyenne'
        > 35   → 'Mauvaise'
    """
    if pd.isna(val):
        return "Inconnu"
    if val < 20:
        return "Bonne"
    elif val < 35:
        return "Moyenne"
    else:
        return "Mauvaise"


# ============================================================================
# ÉTAPE 1 : LECTURE DES DONNÉES (ZONE SILVER)
# ============================================================================

print("ÉTAPE 1 : Lecture des données Silver...")
print("-" * 80)

try:
    df = pd.read_csv(FICHIER_ENTREE, sep=";")
    print(f"✓ Fichier chargé : {len(df)} lignes")
    print(f"✓ Colonnes : {df.columns.tolist()}")
    print()
except Exception as e:
    print(f"✗ Erreur lors de la lecture : {e}")
    exit(1)

print("Aperçu des données Silver :")
print(df.head(10))
print()

# ============================================================================
# ÉTAPE 2 : PRÉPARATION / VÉRIFICATIONS
# ============================================================================

print("ÉTAPE 2 : Préparation des données...")
print("-" * 80)

colonnes_attendues = [
    "date",
    "arrondissement_nom",
    "ninsee",
    "no2",
    "o3",
    "pm10",
    "qualite_air",
    "categorie_no2",
    "categorie_pm10",
    "categorie_o3",
]

manquantes = [col for col in colonnes_attendues if col not in df.columns]
if manquantes:
    print(f"✗ Colonnes manquantes dans le fichier Silver : {manquantes}")
    print("   Vérifie que tu as bien exporté ton CSV avec toutes les colonnes attendues.")
    exit(1)

print("✓ Toutes les colonnes attendues sont présentes.")
print()

# Conversion des types si nécessaire
print("→ Conversion de la colonne 'date' au format datetime (JJ/MM/AAAA)...")
df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

nb_dates_nulles = df["date"].isna().sum()
if nb_dates_nulles > 0:
    print(f"⚠ Attention : {nb_dates_nulles} dates non reconnues (NaT).")
else:
    print("✓ Toutes les dates ont été correctement converties.")
print()

# Ajout colonnes temporelles (année, mois)
df["annee"] = df["date"].dt.year
df["mois"] = df["date"].dt.month

print("→ Colonnes 'annee' et 'mois' ajoutées.")
print(f"✓ Années présentes : {sorted(df['annee'].dropna().unique().tolist())}")
print()

# S'assurer que les colonnes numériques sont bien au bon type
for col in ["no2", "pm10", "o3"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("→ Colonnes no2, pm10, o3 converties en numérique.")
print()

# ============================================================================
# ÉTAPE 3 : AGRÉGATION ANNUELLE (ZONE GOLD - ANNUEL)
# ============================================================================

print("ÉTAPE 3 : Agrégation ANNUELLE (Zone GOLD)...")
print("-" * 80)

group_cols_annual = ["annee", "arrondissement_nom", "ninsee"]

agg_dict_annual = {
    "no2": ["mean", "median", "min", "max"],
    "pm10": ["mean", "median", "min", "max"],
    "o3": ["mean", "median", "min", "max"],
    "qualite_air": get_mode_or_nan,  # qualité majoritaire
}

df_gold_annual = df.groupby(group_cols_annual).agg(agg_dict_annual)

# Aplatir les colonnes multi-index
df_gold_annual.columns = [
    "_".join([c for c in col if c])  # ("no2", "mean") → "no2_mean"
    for col in df_gold_annual.columns.values
]
df_gold_annual = df_gold_annual.reset_index()

# Renommer la qualité majoritaire
if "qualite_air" in df_gold_annual.columns:
    df_gold_annual = df_gold_annual.rename(columns={"qualite_air": "qualite_air_majoritaire"})

# Calcul indice global
print("→ Calcul de l'indice global de pollution (pondération 0.5*NO2 + 0.3*PM10 + 0.2*O3)...")
df_gold_annual["indice_global_pollution"] = (
    0.5 * df_gold_annual["no2_mean"]
    + 0.3 * df_gold_annual["pm10_mean"]
    + 0.2 * df_gold_annual["o3_mean"]
)

# Catégorisation de l'indice global
df_gold_annual["categorie_indice_global"] = df_gold_annual["indice_global_pollution"].apply(
    categoriser_indice_global
)

# Rang par année (1 = plus pollué)
df_gold_annual["rang_pollution_annee"] = (
    df_gold_annual
    .groupby("annee")["indice_global_pollution"]
    .rank(method="dense", ascending=False)
    .astype(int)
)

# Réorganisation des colonnes pour lisibilité
colonnes_ordre_annual = [
    "annee",
    "arrondissement_nom",
    "ninsee",
    "no2_mean", "no2_median", "no2_min", "no2_max",
    "pm10_mean", "pm10_median", "pm10_min", "pm10_max",
    "o3_mean", "o3_median", "o3_min", "o3_max",
    "qualite_air_majoritaire",
    "indice_global_pollution",
    "categorie_indice_global",
    "rang_pollution_annee",
]

colonnes_annual_existantes = [c for c in colonnes_ordre_annual if c in df_gold_annual.columns]
df_gold_annual = df_gold_annual[colonnes_annual_existantes]

print(f"✓ Table GOLD annuelle créée : {len(df_gold_annual)} lignes")
print()

# ============================================================================
# ÉTAPE 4 : AGRÉGATION MENSUELLE (ZONE GOLD - MENSUELLE, OPTIONNEL)
# ============================================================================

print("ÉTAPE 4 : Agrégation MENSUELLE (Zone GOLD)...")
print("-" * 80)

group_cols_monthly = ["annee", "mois", "arrondissement_nom", "ninsee"]

agg_dict_monthly = {
    "no2": "mean",
    "pm10": "mean",
    "o3": "mean",
    "qualite_air": get_mode_or_nan,
}

df_gold_monthly = df.groupby(group_cols_monthly).agg(agg_dict_monthly).reset_index()

df_gold_monthly = df_gold_monthly.rename(columns={
    "no2": "no2_mean",
    "pm10": "pm10_mean",
    "o3": "o3_mean",
    "qualite_air": "qualite_air_majoritaire",
})

df_gold_monthly["indice_global_pollution"] = (
    0.5 * df_gold_monthly["no2_mean"]
    + 0.3 * df_gold_monthly["pm10_mean"]
    + 0.2 * df_gold_monthly["o3_mean"]
)

df_gold_monthly["categorie_indice_global"] = df_gold_monthly["indice_global_pollution"].apply(
    categoriser_indice_global
)

print(f"✓ Table GOLD mensuelle créée : {len(df_gold_monthly)} lignes")
print()

# ============================================================================
# ÉTAPE 5 : SAUVEGARDE
# ============================================================================

print("ÉTAPE 5 : Sauvegarde des fichiers GOLD...")
print("-" * 80)

df_gold_annual.to_csv(FICHIER_SORTIE_ANNUEL, index=False, encoding="utf-8", sep=";")
print(f"✓ Fichier GOLD annuel sauvegardé : {FICHIER_SORTIE_ANNUEL}")

df_gold_monthly.to_csv(FICHIER_SORTIE_MENSUEL, index=False, encoding="utf-8", sep=";")
print(f"✓ Fichier GOLD mensuel sauvegardé : {FICHIER_SORTIE_MENSUEL}")
print()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("=" * 80)
print("RÉSUMÉ FINAL - QUALITÉ DE L'AIR (ZONE GOLD)")
print("=" * 80)
print()

print(f" • Lignes d'entrée (Silver)            : {len(df)}")
print(f" • Lignes sortie Gold ANNUEL           : {len(df_gold_annual)}")
print(f" • Lignes sortie Gold MENSUEL          : {len(df_gold_monthly)}")
print(f" • Arrondissements couverts (annual)   : {df_gold_annual['arrondissement_nom'].nunique()}")
print(f" • Années couvertes                    : {df_gold_annual['annee'].nunique()}")
print()

print(" Top 5 arrondissements les plus pollués (indice global annuel) :")
top5_pollues = df_gold_annual.sort_values("indice_global_pollution", ascending=False).head(5)
for _, row in top5_pollues.iterrows():
    print(f"  - {row['annee']} | {row['arrondissement_nom']} "
          f"(indice = {row['indice_global_pollution']:.2f}, rang = {row['rang_pollution_annee']})")
print()

print("=" * 80)
print("✅ TRANSFORMATION QUALITÉ DE L'AIR TERMINÉE AVEC SUCCÈS !")
print("=" * 80)
print()

print(" Aperçu GOLD ANNUEL (5 premières lignes) :")
print("-" * 80)
print(df_gold_annual.head(5).to_string(index=False))
print()

print(" Aperçu GOLD MENSUEL (5 premières lignes) :")
print("-" * 80)
print(df_gold_monthly.head(5).to_string(index=False))
print()

print(f" Fichiers disponibles :")
print(f"  • {FICHIER_SORTIE_ANNUEL}")
print(f"  • {FICHIER_SORTIE_MENSUEL}")
