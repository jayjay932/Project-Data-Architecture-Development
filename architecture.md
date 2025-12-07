# Architecture & Data Flow

Ce document décrit l’architecture logicielle de **Urban Data Explorer** ainsi que les transformations de données.

## 1. Vision générale

```
           +-------------------+        +------------------+
           |  Données Bronze   |        |   Référentiels   |
           |  (DVF, INSEE, …)  |        |  (Surface, Air)  |
           +---------+---------+        +--------+---------+
                     |                           |
                     v                           v
              etl/clean.py              etl/clean.py (sections dédiées)
                     \_____________________ ___________________/
                                           V
                                 Données Silver (tables nettoyées)
                                           |
                                           v
                                   etl/aggregate.py
                                           |
                                           v
                              data/gold_layer/all_data.csv
                                           |
                                           v
                           backend/app.py (API Flask + Swagger)
                                           |
                                           v
                         frontend (HTML/CSS/JS & MapLibre)
```

## 2. Couches de données

| Couche  | Dossier                                | Description |
|--------|-----------------------------------------|-------------|
| Bronze | `data/bronze_layer/`                    | Extractions brutes (DVF 2020‑2025, socio-éco, qualité de l’air) au format CSV. |
| Silver | `data/silver_layer/`                    | Données nettoyées, normalisées (codes INSEE, surfaces filtrées, indicateurs calculés). |
| Gold   | `data/gold_layer/all_data.csv`          | Table large par `(code_commune, annee)` avec toutes les métriques et parts (typologies, surfaces). Utilisée directement par l’API. |

### Transformations clefs

- **Nettoyage DVF** : suppression des surfaces aberrantes, calcul du prix/m², typologie via `nombre_pieces_principales`.
- **Agrégation** : médian prix, variation vs N‑1, parts typologiques/surfaces, somme des transactions, fusion des indicateurs socio-économiques (revenu médian, logements sociaux, densité, qualité de l’air).
- **City Metrics** : calculés dans `backend/app.py` en sommant tous les arrondissements, utilisés pour les vues “Paris (all)”.

## 3. Backend

- Framework : **Flask**, CORS activé.
- Cache in-memory (Python) pour `PRICE_DATA`, `METRICS_BY_KEY`, `CITY_METRICS`.
- Endpoints principaux :
  - `/api/price`, `/api/price/history`
  - `/api/metrics`, `/api/typology`, `/api/surfaces`
  - `/api/arrondissements`, `/api/arrondissements.geojson`
  - `/api/docs` (Swagger UI) + `/api/docs.json` (OpenAPI)
- Validation : `normalize_arrondissement_code` accepte codes, libellés ou “all”.
- Swagger : défini dans `SWAGGER_SPEC` et servi via un bundle standalone.

## 4. Frontend

- Fichiers : `frontend/index.html`, `frontend/style.css`, `frontend/app.js`.
- **Vue d’ensemble** : Carte MapLibre + popups, KPI, graphe typologie, graphe surfaces.
- **Comparaison** : filtres année/arrondissements, cartes A/B, ligne prix, radar multi-axes (canvas custom).
- **Données** : tableau statique.

### Modules JS (extraits)

| Module | Description |
|--------|-------------|
| `initializeMap` | MapLibre + survols & popups (fetch API). |
| `loadMetrics`   | Chargement des KPI via `/api/metrics`. |
| `renderTypologyChart` / `renderSurfaceChart` | Graphiques canvas + tooltips. |
| `loadPriceTrendHistory` | Graphe ligne “Évolution du prix” filtré par année/arrondissement. |
| `renderComparisonRadar` | Radar multi-axes (prix, revenus, densité, transactions, log. sociaux). |
| Caches (`metricsCache`, `typologyCache`, …) | évitent les rechargements inutiles. |

## 5. Sécurité & performances

- **Front** : pas de dépendances lourdes (MapLibre + canvas custom), rendant l’UI rapide.
- **Back** : aucune base de données, lecture depuis CSV gold. Idéal pour POC/atelier, mais peut être migré vers une base si le volume augmente.
- **Swagger** facilite la découverte API et la gouvernance.
- **Authentification JWT** : activable via `UDE_REQUIRE_AUTH=1` + `UDE_API_SECRET`. Toutes les routes API passent par le décorateur `@require_jwt`, qui vérifie l’en-tête `Authorization: Bearer <token>`. En local, ces variables ne sont pas définies pour simplifier les tests.

## 6. Pistes d’évolution

- Brancher un scheduler pour régénérer la couche gold (Airflow / Prefect).
- Ajouter une vraie base (PostgreSQL/PostGIS) pour gérer l’historique et les jointures.
- Internationalisation du frontend.
- Authentification (JWT) si ouverture publique.
