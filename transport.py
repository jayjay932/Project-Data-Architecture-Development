"""
Script de transformation des données RATP
Objectif : Créer un CSV avec les 20 arrondissements de Paris et leurs lignes de métro/RER

Input : trafic-annuel-entrant-par-station-du-reseau-ferre-2021.csv
Output : arrondissements_lignes_metro_rer.csv
"""

import pandas as pd
import re
from collections import defaultdict

print("="*80)
print("TRANSFORMATION DONNÉES RATP - AGRÉGATION PAR ARRONDISSEMENT")
print("="*80)
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Chemin du fichier d'entrée
FICHIER_ENTREE = r"C:\Users\jason\Downloads\projet_data_architecture\data\bronze\trafic-annuel-entrant-par-station-du-reseau-ferre-2021.csv"

# Chemin du fichier de sortie
FICHIER_SORTIE = "arrondissements_lignes_metro_rer.csv"

print(f" Fichier d'entrée : {FICHIER_ENTREE}")
print(f" Fichier de sortie : {FICHIER_SORTIE}")
print()

# ============================================================================
# ÉTAPE 1 : LECTURE DES DONNÉES
# ============================================================================

print("ÉTAPE 1 : Lecture des données...")
print("-" * 80)

try:
    # Lire le CSV avec point-virgule comme séparateur
    df = pd.read_csv(FICHIER_ENTREE, sep=';', encoding='utf-8')
    print(f"✓ Fichier chargé : {len(df)} lignes")
    print(f"✓ Colonnes : {df.columns.tolist()}")
    print()
except Exception as e:
    print(f"✗ Erreur lors de la lecture : {e}")
    print("Tentative avec un autre encodage...")
    try:
        df = pd.read_csv(FICHIER_ENTREE, sep=';', encoding='latin-1')
        print(f"✓ Fichier chargé avec encodage latin-1 : {len(df)} lignes")
        print()
    except Exception as e2:
        print(f"✗ Erreur : {e2}")
        exit(1)

# Afficher un aperçu
print("Aperçu des données :")
print(df.head(10))
print()

# ============================================================================
# ÉTAPE 2 : FILTRAGE ET NETTOYAGE
# ============================================================================

print("ÉTAPE 2 : Filtrage et nettoyage...")
print("-" * 80)

# Nettoyer les noms de colonnes (supprimer espaces)
df.columns = df.columns.str.strip()

# Filtrer uniquement Paris et les arrondissements valides
print("→ Filtrage des stations parisiennes...")
df_paris = df[df['Ville'].str.strip() == 'Paris'].copy()
print(f"  ✓ {len(df_paris)} stations à Paris")

# Nettoyer la colonne Arrondissement - CORRECTION ICI
def nettoyer_arrondissement(arr):
    """Extrait le numéro d'arrondissement"""
    if pd.isna(arr):
        return None
    arr = str(arr).strip()
    # Extraire les chiffres (ex: "13" de "13" ou "75013")
    match = re.search(r'\d+', arr)
    if match:
        num = int(match.group())
        # Si c'est un code postal (75001-75020), extraire les 2 derniers chiffres
        if num >= 75001 and num <= 75020:
            return num - 75000
        # Si c'est déjà un arrondissement (1-20)
        elif num >= 1 and num <= 20:
            return num
    return None

# CORRECTION : Utiliser le nom correct de la colonne
df_paris['Arrondissement_Num'] = df_paris['Arrondissement pour Paris'].apply(nettoyer_arrondissement)

# Filtrer les arrondissements valides (1-20)
df_paris = df_paris[df_paris['Arrondissement_Num'].notna()].copy()
df_paris['Arrondissement_Num'] = df_paris['Arrondissement_Num'].astype(int)

print(f"→ Stations avec arrondissement valide : {len(df_paris)}")
print(f"→ Arrondissements présents : {sorted(df_paris['Arrondissement_Num'].unique())}")
print()

# ============================================================================
# ÉTAPE 3 : EXTRACTION DES LIGNES
# ============================================================================

print("ÉTAPE 3 : Extraction des lignes de métro/RER...")
print("-" * 80)

def extraire_lignes(row):
    """Extrait toutes les lignes de métro/RER d'une station"""
    lignes = set()
    
    # Colonnes de correspondance
    colonnes_correspondance = ['Correspondance_1', 'Correspondance_2', 'Correspondance_3', 
                               'Correspondance_4', 'Correspondance_5']
    
    for col in colonnes_correspondance:
        if col in row and pd.notna(row[col]):
            ligne = str(row[col]).strip()
            if ligne:
                lignes.add(ligne)
    
    return lignes

# Extraire les lignes pour chaque station
df_paris['Lignes'] = df_paris.apply(extraire_lignes, axis=1)

print(f"✓ Lignes extraites pour {len(df_paris)} stations")
print()

# ============================================================================
# ÉTAPE 4 : AGRÉGATION PAR ARRONDISSEMENT
# ============================================================================

print("ÉTAPE 4 : Agrégation par arrondissement...")
print("-" * 80)

# Dictionnaire pour stocker les résultats
resultats = {}

for arr in range(1, 21):
    # Filtrer les stations de cet arrondissement
    stations_arr = df_paris[df_paris['Arrondissement_Num'] == arr]
    
    if len(stations_arr) > 0:
        # Collecter toutes les lignes uniques
        lignes_metro = set()
        lignes_rer = set()
        
        for _, row in stations_arr.iterrows():
            for ligne in row['Lignes']:
                # Identifier si c'est RER ou Métro
                if 'RER' in ligne.upper() or ligne.upper() in ['A', 'B', 'C', 'D', 'E']:
                    lignes_rer.add(ligne)
                else:
                    # C'est une ligne de métro (numéro)
                    lignes_metro.add(ligne)
        
        # Trier les lignes
        lignes_metro_sorted = sorted(lignes_metro, key=lambda x: (len(x), x))
        lignes_rer_sorted = sorted(lignes_rer)
        
        resultats[arr] = {
            'Arrondissement': arr,
            'Nombre_Stations': len(stations_arr),
            'Trafic_Total': stations_arr['Trafic'].sum(),
            'Lignes_Metro': ', '.join(lignes_metro_sorted) if lignes_metro_sorted else '',
            'Lignes_RER': ', '.join(lignes_rer_sorted) if lignes_rer_sorted else '',
            'Nombre_Lignes_Metro': len(lignes_metro_sorted),
            'Nombre_Lignes_RER': len(lignes_rer_sorted),
            'Toutes_Lignes': ', '.join(sorted(lignes_metro_sorted + lignes_rer_sorted, key=lambda x: (len(x), x)))
        }
        
        print(f"  Arrondissement {arr:2d} : {len(stations_arr):3d} stations, "
              f"{len(lignes_metro_sorted):2d} lignes métro, {len(lignes_rer_sorted):2d} lignes RER")
    else:
        # Arrondissement sans station dans les données
        resultats[arr] = {
            'Arrondissement': arr,
            'Nombre_Stations': 0,
            'Trafic_Total': 0,
            'Lignes_Metro': '',
            'Lignes_RER': '',
            'Nombre_Lignes_Metro': 0,
            'Nombre_Lignes_RER': 0,
            'Toutes_Lignes': ''
        }
        print(f"  Arrondissement {arr:2d} : Aucune station")

print()

# ============================================================================
# ÉTAPE 5 : CRÉATION DU DATAFRAME FINAL
# ============================================================================

print("ÉTAPE 5 : Création du DataFrame final...")
print("-" * 80)

# Convertir le dictionnaire en DataFrame
df_final = pd.DataFrame.from_dict(resultats, orient='index')

# Trier par arrondissement
df_final = df_final.sort_values('Arrondissement')

# Réorganiser les colonnes
colonnes_ordre = [
    'Arrondissement',
    'Nombre_Stations',
    'Trafic_Total',
    'Nombre_Lignes_Metro',
    'Nombre_Lignes_RER',
    'Lignes_Metro',
    'Lignes_RER',
    'Toutes_Lignes'
]

df_final = df_final[colonnes_ordre]

# Formater le trafic
df_final['Trafic_Total'] = df_final['Trafic_Total'].astype(int)

print(f"✓ DataFrame créé : {len(df_final)} arrondissements")
print()

# ============================================================================
# ÉTAPE 6 : SAUVEGARDE
# ============================================================================

print("ÉTAPE 6 : Sauvegarde du fichier...")
print("-" * 80)

# Sauvegarder en CSV
df_final.to_csv(FICHIER_SORTIE, index=False, encoding='utf-8-sig', sep=';')
print(f"✓ Fichier sauvegardé : {FICHIER_SORTIE}")
print()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("="*80)
print("RÉSUMÉ FINAL")
print("="*80)
print()

print(f" Statistiques globales :")
print(f"  • Total arrondissements : {len(df_final)}")
print(f"  • Arrondissements avec stations : {(df_final['Nombre_Stations'] > 0).sum()}")
print(f"  • Total stations à Paris : {df_final['Nombre_Stations'].sum()}")
print(f"  • Trafic total : {df_final['Trafic_Total'].sum():,} voyageurs")
print()

print(f" Top 5 arrondissements par trafic :")
top5_trafic = df_final.nlargest(5, 'Trafic_Total')
for _, row in top5_trafic.iterrows():
    print(f"  {int(row['Arrondissement']):2d}e : {int(row['Trafic_Total']):>12,} voyageurs "
          f"({int(row['Nombre_Stations'])} stations)")
print()

print(f" Top 5 arrondissements par nombre de lignes :")
df_final['Total_Lignes'] = df_final['Nombre_Lignes_Metro'] + df_final['Nombre_Lignes_RER']
top5_lignes = df_final.nlargest(5, 'Total_Lignes')
for _, row in top5_lignes.iterrows():
    print(f"  {int(row['Arrondissement']):2d}e : {int(row['Total_Lignes'])} lignes "
          f"(Métro: {int(row['Nombre_Lignes_Metro'])}, RER: {int(row['Nombre_Lignes_RER'])})")
print()

print("="*80)
print("✅ TRANSFORMATION TERMINÉE AVEC SUCCÈS !")
print("="*80)
print()

# Afficher un aperçu du résultat
print(" APERÇU DU RÉSULTAT (10 premières lignes) :")
print("-" * 80)
print(df_final.head(10).to_string(index=False))
print()

print(f" Fichier disponible : {FICHIER_SORTIE}")