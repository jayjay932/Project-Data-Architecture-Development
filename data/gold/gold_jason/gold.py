"""
Script d'agrégation complète des données par arrondissement de Paris
Produit UN SEUL CSV : 


Métriques incluses :
- Prix/m² médian et évolution temporelle
- Valeur médiane des ventes
- Typologie des logements (appartements/maisons/pièces)
- Transport (métro/RER)
- Qualité de l'air (pollution)
- Statistiques démographiques
"""

import pandas as pd
import numpy as np
import re
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

print("="*100)
print("CRÉATION DU DASHBOARD COMPLET PAR ARRONDISSEMENT - PARIS")
print("="*100)
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_PATH = r"C:\Users\jason\Downloads\projet_data_architecture\data\silver"
FICHIER_SORTIE = "dashboard_arrondissements_paris2.csv"

ANNEES = [2020, 2021, 2022, 2023, 2024, 2025]

print(f"📂 Répertoire : {BASE_PATH}")
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

# ============================================================================
# ÉTAPE 1 : DONNÉES IMMOBILIÈRES (2020-2025)
# ============================================================================

print("ÉTAPE 1 : Chargement des données immobilières...")
print("-" * 100)

donnees_immo_par_annee = {}

for annee in ANNEES:
    fichier_clean = f"{BASE_PATH}\\75_{annee}_clean.csv"
    fichier_lots = f"{BASE_PATH}\\75_{annee}_lots.csv"
    
    try:
        # Charger fichier clean
        df_clean = pd.read_csv(fichier_clean, sep=',', low_memory=False)
        print(f"  ✓ {annee} clean : {len(df_clean)} lignes")
        
        # Extraire arrondissement
        if 'code_postal' in df_clean.columns:
            df_clean['arrondissement'] = df_clean['code_postal'].apply(extraire_arrondissement)
        elif 'nom_commune' in df_clean.columns:
            df_clean['arrondissement'] = df_clean['nom_commune'].apply(extraire_arrondissement_nom)
        
        # Filtrer arrondissements valides
        df_clean = df_clean[df_clean['arrondissement'].notna()].copy()
        
        # Charger lots pour avoir les surfaces
        try:
            df_lots = pd.read_csv(fichier_lots, sep=',', low_memory=False)
            # Joindre avec les lots
            if 'id_mutation' in df_clean.columns and 'id_mutation' in df_lots.columns:
                df_clean = df_clean.merge(
                    df_lots[['id_mutation', 'surface_carrez']].drop_duplicates(),
                    on='id_mutation',
                    how='left'
                )
        except:
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

# DataFrame final
resultats = {}

for arr in range(1, 21):
    resultats[arr] = {
        'Arrondissement': arr
    }

# Pour chaque année
for annee in ANNEES:
    if annee not in donnees_immo_par_annee:
        continue
    
    df = donnees_immo_par_annee[annee]
    
    print(f"\n  [{annee}] Agrégation...")
    
    for arr in range(1, 21):
        df_arr = df[df['arrondissement'] == arr].copy()
        
        if len(df_arr) == 0:
            resultats[arr][f'nb_ventes_{annee}'] = 0
            resultats[arr][f'prix_median_{annee}'] = None
            resultats[arr][f'prix_m2_median_{annee}'] = None
            continue
        
        # Filtrer uniquement les ventes (pas Echange, Donation, etc.)
        if 'nature_mutation' in df_arr.columns:
            df_arr = df_arr[df_arr['nature_mutation'] == 'Vente']
        
        # Filtrer uniquement les appartements pour le prix/m²
        df_appart = df_arr[
            (df_arr['type_local'] == 'Appartement') if 'type_local' in df_arr.columns else df_arr.index
        ].copy()
        
        # Nombre de ventes
        resultats[arr][f'nb_ventes_{annee}'] = len(df_arr)
        
        # Prix médian
        if 'valeur_fonciere' in df_arr.columns:
            prix_valides = df_arr['valeur_fonciere'].dropna()
            prix_valides = prix_valides[(prix_valides > 10000) & (prix_valides < 10000000)]
            if len(prix_valides) > 0:
                resultats[arr][f'prix_median_{annee}'] = int(prix_valides.median())
            else:
                resultats[arr][f'prix_median_{annee}'] = None
        
        # Prix/m² médian
        prix_m2_list = []
        for _, row in df_appart.iterrows():
            if 'valeur_fonciere' in row and 'surface_reelle_bati' in row:
                if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface_reelle_bati']):
                    if row['surface_reelle_bati'] > 0:
                        prix_m2 = row['valeur_fonciere'] / row['surface_reelle_bati']
                        if 3000 < prix_m2 < 50000:  # Filtrer les valeurs aberrantes
                            prix_m2_list.append(prix_m2)
            elif 'valeur_fonciere' in row and 'surface_carrez' in row:
                if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface_carrez']):
                    if row['surface_carrez'] > 0:
                        prix_m2 = row['valeur_fonciere'] / row['surface_carrez']
                        if 3000 < prix_m2 < 50000:
                            prix_m2_list.append(prix_m2)
        
        if len(prix_m2_list) > 0:
            resultats[arr][f'prix_m2_median_{annee}'] = int(np.median(prix_m2_list))
        else:
            resultats[arr][f'prix_m2_median_{annee}'] = None
        
        print(f"    Arr. {arr:2d} : {len(df_arr):4d} ventes, "
              f"Prix: {resultats[arr][f'prix_median_{annee}'] or 0:>9,}€, "
              f"Prix/m²: {resultats[arr][f'prix_m2_median_{annee}'] or 0:>6,}€/m²")

print()

# ============================================================================
# ÉTAPE 3 : ÉVOLUTION TEMPORELLE DÉTAILLÉE
# ============================================================================

print("ÉTAPE 3 : Calcul des évolutions temporelles...")
print("-" * 100)

for arr in range(1, 21):
    # ========================================================================
    # 3.1 - ÉVOLUTION GLOBALE (2020 vs 2024)
    # ========================================================================
    
    # Évolution prix médian (2020 vs 2024)
    prix_2020 = resultats[arr].get('prix_median_2020')
    prix_2024 = resultats[arr].get('prix_median_2024')
    
    if prix_2020 and prix_2024 and prix_2020 > 0:
        evolution_pct = ((prix_2024 - prix_2020) / prix_2020) * 100
        resultats[arr]['evolution_prix_2020_2024_pct'] = round(evolution_pct, 1)
    else:
        resultats[arr]['evolution_prix_2020_2024_pct'] = None
    
    # Évolution prix/m² (2020 vs 2024)
    prixm2_2020 = resultats[arr].get('prix_m2_median_2020')
    prixm2_2024 = resultats[arr].get('prix_m2_median_2024')
    
    if prixm2_2020 and prixm2_2024 and prixm2_2020 > 0:
        evolution_pct = ((prixm2_2024 - prixm2_2020) / prixm2_2020) * 100
        resultats[arr]['evolution_prix_m2_2020_2024_pct'] = round(evolution_pct, 1)
    else:
        resultats[arr]['evolution_prix_m2_2020_2024_pct'] = None
    
    # ========================================================================
    # 3.2 - ÉVOLUTIONS ANNÉE PAR ANNÉE (Prix médian)
    # ========================================================================
    
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]
        
        prix_actuel = resultats[arr].get(f'prix_median_{annee_actuelle}')
        prix_suivant = resultats[arr].get(f'prix_median_{annee_suivante}')
        
        if prix_actuel and prix_suivant and prix_actuel > 0:
            evolution_annuelle = ((prix_suivant - prix_actuel) / prix_actuel) * 100
            resultats[arr][f'evolution_prix_{annee_actuelle}_{annee_suivante}_pct'] = round(evolution_annuelle, 1)
        else:
            resultats[arr][f'evolution_prix_{annee_actuelle}_{annee_suivante}_pct'] = None
    
    # ========================================================================
    # 3.3 - ÉVOLUTIONS ANNÉE PAR ANNÉE (Prix/m²)
    # ========================================================================
    
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]
        
        prixm2_actuel = resultats[arr].get(f'prix_m2_median_{annee_actuelle}')
        prixm2_suivant = resultats[arr].get(f'prix_m2_median_{annee_suivante}')
        
        if prixm2_actuel and prixm2_suivant and prixm2_actuel > 0:
            evolution_annuelle = ((prixm2_suivant - prixm2_actuel) / prixm2_actuel) * 100
            resultats[arr][f'evolution_prix_m2_{annee_actuelle}_{annee_suivante}_pct'] = round(evolution_annuelle, 1)
        else:
            resultats[arr][f'evolution_prix_m2_{annee_actuelle}_{annee_suivante}_pct'] = None
    
    # ========================================================================
    # 3.4 - TENDANCE GÉNÉRALE (Prix/m²)
    # ========================================================================
    
    # Calculer la tendance sur la période 2020-2024
    prix_m2_series = []
    annees_valides = []
    
    for annee in ANNEES:
        prix_m2 = resultats[arr].get(f'prix_m2_median_{annee}')
        if prix_m2:
            prix_m2_series.append(prix_m2)
            annees_valides.append(annee)
    
    if len(prix_m2_series) >= 3:  # Au moins 3 points pour déterminer une tendance
        # Calcul de la pente moyenne
        evolutions = []
        for i in range(len(prix_m2_series) - 1):
            if prix_m2_series[i] > 0:
                evol = ((prix_m2_series[i+1] - prix_m2_series[i]) / prix_m2_series[i]) * 100
                evolutions.append(evol)
        
        if evolutions:
            moyenne_evolution = np.mean(evolutions)
            
            # Déterminer la tendance
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
            
            resultats[arr]['tendance_prix_m2'] = tendance
            resultats[arr]['evolution_annuelle_moyenne_pct'] = round(moyenne_evolution, 1)
            
            # Volatilité (écart-type des évolutions)
            if len(evolutions) > 1:
                volatilite = np.std(evolutions)
                resultats[arr]['volatilite_prix_m2'] = round(volatilite, 1)
            else:
                resultats[arr]['volatilite_prix_m2'] = None
        else:
            resultats[arr]['tendance_prix_m2'] = "Données insuffisantes"
            resultats[arr]['evolution_annuelle_moyenne_pct'] = None
            resultats[arr]['volatilite_prix_m2'] = None
    else:
        resultats[arr]['tendance_prix_m2'] = "Données insuffisantes"
        resultats[arr]['evolution_annuelle_moyenne_pct'] = None
        resultats[arr]['volatilite_prix_m2'] = None
    
    # ========================================================================
    # 3.5 - ÉVOLUTIONS VOLUME DE VENTES
    # ========================================================================
    
    for i in range(len(ANNEES) - 1):
        annee_actuelle = ANNEES[i]
        annee_suivante = ANNEES[i + 1]
        
        nb_ventes_actuel = resultats[arr].get(f'nb_ventes_{annee_actuelle}')
        nb_ventes_suivant = resultats[arr].get(f'nb_ventes_{annee_suivante}')
        
        if nb_ventes_actuel and nb_ventes_suivant and nb_ventes_actuel > 0:
            evolution_volume = ((nb_ventes_suivant - nb_ventes_actuel) / nb_ventes_actuel) * 100
            resultats[arr][f'evolution_volume_{annee_actuelle}_{annee_suivante}_pct'] = round(evolution_volume, 1)
        else:
            resultats[arr][f'evolution_volume_{annee_actuelle}_{annee_suivante}_pct'] = None

print("  ✓ Évolutions temporelles détaillées calculées")
print("    - Évolutions globales 2020-2024")
print("    - Évolutions année par année (prix, prix/m², volume)")
print("    - Tendances et volatilité")
print()

# ============================================================================
# ÉTAPE 4 : TYPOLOGIE DES LOGEMENTS
# ============================================================================

print("ÉTAPE 4 : Analyse de la typologie des logements...")
print("-" * 100)

# Utiliser les données les plus récentes (2024)
if 2024 in donnees_immo_par_annee:
    df_typo = donnees_immo_par_annee[2024]
    
    for arr in range(1, 21):
        df_arr = df_typo[df_typo['arrondissement'] == arr]
        
        # Types de logements
        if 'type_local' in df_arr.columns:
            nb_appart = len(df_arr[df_arr['type_local'] == 'Appartement'])
            nb_maison = len(df_arr[df_arr['type_local'] == 'Maison'])
            total = nb_appart + nb_maison
            
            resultats[arr]['nb_appartements_2024'] = nb_appart
            resultats[arr]['nb_maisons_2024'] = nb_maison
            
            if total > 0:
                resultats[arr]['pct_appartements'] = round((nb_appart / total) * 100, 1)
            else:
                resultats[arr]['pct_appartements'] = None
        
        # Nombre de pièces moyen
        if 'nombre_pieces_principales' in df_arr.columns:
            pieces = df_arr['nombre_pieces_principales'].dropna()
            pieces = pieces[(pieces > 0) & (pieces < 10)]
            if len(pieces) > 0:
                resultats[arr]['nb_pieces_moyen'] = round(pieces.mean(), 1)
            else:
                resultats[arr]['nb_pieces_moyen'] = None

print("  ✓ Typologie analysée")
print()

# ============================================================================
# ÉTAPE 5 : DONNÉES TRANSPORT
# ============================================================================

print("ÉTAPE 5 : Chargement des données transport...")
print("-" * 100)

try:
    df_transport = pd.read_csv(f"{BASE_PATH}\\arrondissements_lignes_metro_rer.csv", sep=';')
    print(f"  ✓ Transport chargé : {len(df_transport)} lignes")
    
    for _, row in df_transport.iterrows():
        arr = int(row['Arrondissement'])
        if arr in resultats:
            resultats[arr]['nb_stations_metro'] = int(row['Nombre_Stations'])
            resultats[arr]['trafic_total_metro'] = int(row['Trafic_Total'])
            resultats[arr]['nb_lignes_metro'] = int(row['Nombre_Lignes_Metro'])
            resultats[arr]['nb_lignes_rer'] = int(row['Nombre_Lignes_RER'])
            resultats[arr]['lignes_metro'] = str(row['Lignes_Metro'])
            resultats[arr]['lignes_rer'] = str(row['Lignes_RER'])
    
    print("  ✓ Données transport intégrées")
except Exception as e:
    print(f"  ⚠ Erreur transport : {e}")

print()

# ============================================================================
# ÉTAPE 6 : QUALITÉ DE L'AIR
# ============================================================================

print("ÉTAPE 6 : Chargement des données qualité de l'air...")
print("-" * 100)

try:
    df_air = pd.read_csv(f"{BASE_PATH}\\air_quality_paris_final.csv", sep=',')
    print(f"  ✓ Qualité air chargée : {len(df_air)} lignes")
    
    # Extraire arrondissement
    df_air['arrondissement'] = df_air['arrondissement_nom'].apply(extraire_arrondissement_nom)
    
    # Si pas de colonne ninsee, utiliser arrondissement_nom
    if 'ninsee' not in df_air.columns and 'arrondissement_nom' in df_air.columns:
        df_air['arrondissement'] = df_air['arrondissement_nom'].apply(extraire_arrondissement_nom)
    
    # Moyennes par arrondissement (toutes dates confondues)
    for arr in range(1, 21):
        df_arr = df_air[df_air['arrondissement'] == arr]
        
        if len(df_arr) > 0:
            # Moyennes des polluants
            if 'no2' in df_arr.columns:
                resultats[arr]['no2_moyen'] = round(df_arr['no2'].mean(), 1)
            if 'pm10' in df_arr.columns:
                resultats[arr]['pm10_moyen'] = round(df_arr['pm10'].mean(), 1)
            if 'o3' in df_arr.columns:
                resultats[arr]['o3_moyen'] = round(df_arr['o3'].mean(), 1)
            
            # Qualité dominante
            if 'qualite_air' in df_arr.columns:
                qualite_counts = df_arr['qualite_air'].value_counts()
                if len(qualite_counts) > 0:
                    resultats[arr]['qualite_air_dominante'] = qualite_counts.index[0]
    
    print("  ✓ Données qualité air intégrées")
except Exception as e:
    print(f"  ⚠ Erreur qualité air : {e}")

print()

# ============================================================================
# ÉTAPE 7 : STATISTIQUES COMMUNES
# ============================================================================

print("ÉTAPE 7 : Chargement des statistiques communes...")
print("-" * 100)

try:
    df_stats = pd.read_csv(f"{BASE_PATH}\\stats_commune_2014_2020.csv", sep=',')
    print(f"  ✓ Stats communes chargées : {len(df_stats)} lignes")
    
    # Prendre les données les plus récentes (2020)
    df_stats_2020 = df_stats[df_stats['anneemut'] == 2020]
    
    # Extraire arrondissement depuis codgeo_2020 ou nom_commune
    if 'codgeo_2020' in df_stats_2020.columns:
        df_stats_2020['arrondissement'] = df_stats_2020['codgeo_2020'].apply(extraire_arrondissement_insee)
    elif 'nom_commune' in df_stats_2020.columns:
        df_stats_2020['arrondissement'] = df_stats_2020['nom_commune'].apply(extraire_arrondissement_nom)
    
    for arr in range(1, 21):
        df_arr = df_stats_2020[df_stats_2020['arrondissement'] == arr]
        
        if len(df_arr) > 0:
            row = df_arr.iloc[0]
            
            # Population
            if 'POP_2018' in row:
                resultats[arr]['population_2018'] = int(row['POP_2018']) if pd.notna(row['POP_2018']) else None
            
            # Ménages
            if 'Nbre-menages_2018' in row:
                resultats[arr]['nb_menages_2018'] = int(row['Nbre-menages_2018']) if pd.notna(row['Nbre-menages_2018']) else None
            
            # Logements
            if 'Logement_2018' in row:
                resultats[arr]['nb_logements_2018'] = int(row['Logement_2018']) if pd.notna(row['Logement_2018']) else None
            
            # Prix/m² médian ventea depuis stats (pour comparaison)
            if 'vfm2_ventea' in row:
                resultats[arr]['prix_m2_stats_2020'] = int(row['vfm2_ventea']) if pd.notna(row['vfm2_ventea']) else None
    
    print("  ✓ Statistiques communes intégrées")
except Exception as e:
    print(f"  ⚠ Erreur stats communes : {e}")

print()

# ============================================================================
# ÉTAPE 8 : LOGEMENTS SOCIAUX (Estimation)
# ============================================================================

print("ÉTAPE 8 : Estimation des logements sociaux...")
print("-" * 100)

# Note : Les données de logements sociaux ne sont pas disponibles directement
# On peut faire une estimation basée sur les prix/m² relativement bas
# Les arrondissements avec des prix/m² inférieurs à la médiane parisienne
# ont généralement plus de logements sociaux

prix_m2_paris = []
for arr in range(1, 21):
    if resultats[arr].get('prix_m2_median_2024'):
        prix_m2_paris.append(resultats[arr]['prix_m2_median_2024'])

if len(prix_m2_paris) > 0:
    mediane_paris = np.median(prix_m2_paris)
    
    for arr in range(1, 21):
        prix_arr = resultats[arr].get('prix_m2_median_2024')
        
        if prix_arr:
            # Estimation simplifiée : plus le prix est bas, plus il y a potentiellement de social
            if prix_arr < mediane_paris * 0.7:
                resultats[arr]['estimation_logement_social_pct'] = 'Élevé (>20%)'
            elif prix_arr < mediane_paris * 0.85:
                resultats[arr]['estimation_logement_social_pct'] = 'Moyen (10-20%)'
            else:
                resultats[arr]['estimation_logement_social_pct'] = 'Faible (<10%)'
        else:
            resultats[arr]['estimation_logement_social_pct'] = 'Non estimé'

print("  ✓ Estimations calculées (basées sur prix/m²)")
print()

# ============================================================================
# ÉTAPE 9 : CRÉATION DU DATAFRAME FINAL
# ============================================================================

print("ÉTAPE 9 : Création du DataFrame final...")
print("-" * 100)

df_final = pd.DataFrame.from_dict(resultats, orient='index')
df_final = df_final.sort_values('Arrondissement')

# Réorganiser les colonnes dans un ordre logique
colonnes_ordre = ['Arrondissement']

# Prix et évolutions
for annee in ANNEES:
    colonnes_ordre.extend([
        f'nb_ventes_{annee}',
        f'prix_median_{annee}',
        f'prix_m2_median_{annee}'
    ])

colonnes_ordre.extend([
    'evolution_prix_2020_2024_pct',
    'evolution_prix_m2_2020_2024_pct'
])

# Évolutions année par année - Prix médian
for i in range(len(ANNEES) - 1):
    colonnes_ordre.append(f'evolution_prix_{ANNEES[i]}_{ANNEES[i+1]}_pct')

# Évolutions année par année - Prix/m²
for i in range(len(ANNEES) - 1):
    colonnes_ordre.append(f'evolution_prix_m2_{ANNEES[i]}_{ANNEES[i+1]}_pct')

# Évolutions volume de ventes
for i in range(len(ANNEES) - 1):
    colonnes_ordre.append(f'evolution_volume_{ANNEES[i]}_{ANNEES[i+1]}_pct')

# Tendances et volatilité
colonnes_ordre.extend([
    'tendance_prix_m2',
    'evolution_annuelle_moyenne_pct',
    'volatilite_prix_m2'
])

# Typologie
colonnes_ordre.extend([
    'nb_appartements_2024',
    'nb_maisons_2024',
    'pct_appartements',
    'nb_pieces_moyen'
])

# Logements sociaux
colonnes_ordre.append('estimation_logement_social_pct')

# Transport
colonnes_ordre.extend([
    'nb_stations_metro',
    'trafic_total_metro',
    'nb_lignes_metro',
    'nb_lignes_rer',
    'lignes_metro',
    'lignes_rer'
])

# Qualité de l'air
colonnes_ordre.extend([
    'no2_moyen',
    'pm10_moyen',
    'o3_moyen',
    'qualite_air_dominante'
])

# Démographie
colonnes_ordre.extend([
    'population_2018',
    'nb_menages_2018',
    'nb_logements_2018',
    'prix_m2_stats_2020'
])

# Garder uniquement les colonnes qui existent
colonnes_presentes = [col for col in colonnes_ordre if col in df_final.columns]
autres_colonnes = [col for col in df_final.columns if col not in colonnes_presentes]
df_final = df_final[colonnes_presentes + autres_colonnes]

print(f"  ✓ DataFrame créé : {len(df_final)} arrondissements × {len(df_final.columns)} colonnes")
print()

# ============================================================================
# ÉTAPE 10 : SAUVEGARDE
# ============================================================================

print("ÉTAPE 10 : Sauvegarde du fichier CSV...")
print("-" * 100)

df_final.to_csv(FICHIER_SORTIE, index=False, encoding='utf-8-sig', sep=';')
print(f"  ✓ Fichier sauvegardé : {FICHIER_SORTIE}")
print()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("="*100)
print("RÉSUMÉ FINAL")
print("="*100)
print()

print(f"📊 DASHBOARD CRÉÉ : {FICHIER_SORTIE}")
print(f"   • {len(df_final)} arrondissements")
print(f"   • {len(df_final.columns)} colonnes de données")
print()

print("📈 MÉTRIQUES INCLUSES :")
print()

print("  1️⃣  IMMOBILIER (2020-2025)")
print("     • Nombre de ventes par an")
print("     • Prix médian par an")
print("     • Prix/m² médian par an")
print("     • Évolution 2020-2024 (prix et prix/m²)")
print()

print("  2️⃣  TYPOLOGIE DES LOGEMENTS")
print("     • Nombre d'appartements et maisons")
print("     • % d'appartements")
print("     • Nombre moyen de pièces")
print()

print("  3️⃣  LOGEMENTS SOCIAUX")
print("     • Estimation du % de logements sociaux")
print()

print("  4️⃣  TRANSPORT")
print("     • Nombre de stations de métro")
print("     • Trafic total annuel")
print("     • Nombre de lignes (métro + RER)")
print("     • Liste des lignes")
print()

print("  5️⃣  QUALITÉ DE L'AIR")
print("     • NO2 moyen (μg/m³)")
print("     • PM10 moyen (μg/m³)")
print("     • O3 moyen (μg/m³)")
print("     • Qualité dominante")
print()

print("  6️⃣  DÉMOGRAPHIE")
print("     • Population 2018")
print("     • Nombre de ménages")
print("     • Nombre de logements")
print()

print("🏆 TOP 5 ARRONDISSEMENTS :")
print()

# Top 5 par prix/m² 2024
if 'prix_m2_median_2024' in df_final.columns:
    print("  Prix/m² les plus élevés (2024) :")
    top5_prix = df_final.nlargest(5, 'prix_m2_median_2024')
    for idx, row in top5_prix.iterrows():
        print(f"    {int(row['Arrondissement']):2d}e : {int(row['prix_m2_median_2024']):>6,}€/m²")
    print()

# Top 5 par évolution
if 'evolution_prix_m2_2020_2024_pct' in df_final.columns:
    print("  Plus forte hausse de prix/m² (2020-2024) :")
    top5_evol = df_final.nlargest(5, 'evolution_prix_m2_2020_2024_pct')
    for idx, row in top5_evol.iterrows():
        if pd.notna(row['evolution_prix_m2_2020_2024_pct']):
            tendance = row.get('tendance_prix_m2', 'N/A')
            print(f"    {int(row['Arrondissement']):2d}e : +{row['evolution_prix_m2_2020_2024_pct']:>5.1f}% | Tendance: {tendance}")
    print()

# Arrondissements avec tendances différentes
print("  Tendances de marché :")
if 'tendance_prix_m2' in df_final.columns:
    tendances_count = df_final['tendance_prix_m2'].value_counts()
    for tendance, count in tendances_count.items():
        print(f"    {tendance:20s} : {count} arrondissements")
    print()

# Volatilité
if 'volatilite_prix_m2' in df_final.columns:
    print("  Arrondissements les plus volatils (variation prix/m²) :")
    top5_vol = df_final.nlargest(5, 'volatilite_prix_m2')
    for idx, row in top5_vol.iterrows():
        if pd.notna(row.get('volatilite_prix_m2')):
            print(f"    {int(row['Arrondissement']):2d}e : {row['volatilite_prix_m2']:>5.1f}% de volatilité")
    print()

# Top 5 par nombre de lignes
if 'nb_lignes_metro' in df_final.columns and 'nb_lignes_rer' in df_final.columns:
    df_final['total_lignes'] = df_final['nb_lignes_metro'] + df_final['nb_lignes_rer']
    print("  Meilleure desserte (métro + RER) :")
    top5_transport = df_final.nlargest(5, 'total_lignes')
    for idx, row in top5_transport.iterrows():
        print(f"    {int(row['Arrondissement']):2d}e : {int(row['total_lignes'])} lignes "
              f"({int(row['nb_lignes_metro'])} métro + {int(row['nb_lignes_rer'])} RER)")
    print()

print("="*100)
print("✅ DASHBOARD CRÉÉ AVEC SUCCÈS !")
print("="*100)
print()

print(f"💾 Fichier disponible : {FICHIER_SORTIE}")
print()

# Afficher aperçu
print("📋 APERÇU DES DONNÉES (5 premiers arrondissements) :")
print("-" * 100)

# Colonnes clés pour l'aperçu
colonnes_apercu = [
    'Arrondissement',
    'prix_m2_median_2024',
    'evolution_prix_m2_2020_2024_pct',
    'nb_pieces_moyen',
    'nb_lignes_metro',
    'no2_moyen'
]

colonnes_apercu_presentes = [col for col in colonnes_apercu if col in df_final.columns]
print(df_final[colonnes_apercu_presentes].head().to_string(index=False))
print()