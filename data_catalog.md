# Data Catalog & Sources

Ce document synthétise les données utilisées par Urban Data Explorer, leur provenance et les choix méthodologiques.

## Vue d’ensemble

| Couche | Fichier | Description | Provenance / Justification |
|--------|---------|-------------|----------------------------|
| Bronze | `data/bronze_layer/dvf_75_20xx.csv` | Transactions immobilières (DVF) par année. | Données ouvertes DVF (DGFiP). Base de vérité pour prix/m², typologies, surfaces. |
| Bronze | `data/bronze_layer/*.csv` (revenus, logements sociaux, qualité de l’air, densité) | Indicateurs socio-éco et environnementaux agrégés par arrondissement. | INSEE, Mairie de Paris, Airparif : nécessaires pour contextualiser le marché. |
| Silver | `data/silver_layer/cleaned_*.csv` | Données brutes nettoyées/normalisées (codes INSEE, formats numériques). | Étape intermédiaire pour sécuriser les calculs (suppression outliers, conversions). |
| Gold | `data/gold_layer/all_data.csv` | Table finale prête à servir l’API (prix, variations, typologies, surfaces, socio-éco). | Point d’entrée unique côté backend. |

## Détails par source

### DVF (Demandes de Valeurs Foncières)
- **Champs utilisés** : `valeur_fonciere`, `surface_reelle_bati`, `nombre_pieces_principales`, `code_commune`, `annee`.
- **Nettoyage** : suppression surfaces aberrantes (maison <10 m², appart >200 m²), calcul du `prix_m2`.
- **Justification** : mesure de référence pour les prix immobiliers, couplée à la typologie des biens.

### Revenus médians (INSEE)
- Agrégé par arrondissement (`revenu_median`).
- Utilisé pour l’indicateur socio-économique et les cartes de comparaison.

### Taux de logements sociaux (Mairie de Paris)
- Champ `tx_logement_sociaux`.
- Utile pour suivre la mixité sociale et comparer avec SRU.

### Densité & population (INSEE + surface officielle)
- `densite_population` = population / surface (`superficie_km2`).
- Permet de comparer les territoires fortement urbanisés vs résidentiels.

### Qualité de l’air (Airparif / Mairie de Paris)
- Champs : `air_quality_global`, `no2`, `pm10`, `o3` et leurs qualificatifs.
- Affiché dans les KPI et popups cartographiques.

### Agrégations calculées

| Indicateur | Description |
|------------|-------------|
| `transactions_total` | Somme DVF par arrondissement/année. |
| `transactions_{studio_t1..t5_plus}` | Nombre de transactions par typologie. |
| `part_{studio_t1..t5_plus}` | Part (%) des transactions par typologie. |
| `transactions_surface_*` | Nombre de transactions par classe de surface (<20, 20‑40, ...). |
| `part_surface_*` | Part (%) correspondante. |
| `variation` | (Prix année N – Prix N‑1) / Prix N‑1. |

Ces indicateurs internes sont justifiés car ils apportent des insights au-delà des simples valeurs brutes (structure du parc, segments dominants, tension du marché).

## Gouvernance & Qualité

- **Normalisation codes INSEE** (`zfill(5)`) pour éviter les problèmes de jointure.
- **Dates** : toutes les métriques sont indexées par `annee` pour garantir la comparer entre périodes.
- **Cache API** : in-memory (backend et frontend) pour garantir des temps de réponse rapides sans recalcul.
- **Swagger/OpenAPI** documente les schémas; option JWT (`UDE_REQUIRE_AUTH`) permet de sécuriser l’accès sans impacter les utilisateurs internes.

## Limites connues

- Données DVF limitées jusqu’en 2025 (les années suivantes nécessiteront une nouvelle ingestion).
- Pas de données géographiques fines (quartiers IRIS) – extension possible.
- L’API repose sur CSV en mémoire; envisager une base pour scalabilité (voir `architecture.md`).
