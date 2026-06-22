# Architecture & Data Flow

Ce document décrit l'architecture logicielle actuelle de **Urban Data Explorer** après l'ajout du backend NoSQL optionnel.

## 1. Vue d'ensemble

Le projet repose sur une logique simple :

1. Les données brutes sont nettoyées dans l'ETL.
2. Les données nettoyées sont agrégées dans une couche `gold`.
3. La couche `gold` est servie par l'API Flask.
4. L'API peut lire soit les CSV `gold`, soit MongoDB.
5. Le frontend consomme l'API pour afficher la carte, les KPI et les graphiques.

## 2. Schéma global

```text
                   +-------------------+        +------------------+
                   |  Données Bronze   |        |   Référentiels   |
                   |  (DVF, INSEE, …)  |        |  (Air, Surface)  |
                   +---------+---------+        +--------+---------+
                             |                           |
                             v                           v
                        etl/clean.py          etl/clean.py (sections dédiées)
                             \_____________________ ___________________/
                                                   v
                                      Données Silver (CSV nettoyés)
                                                   |
                                                   v
                                           etl/aggregate.py
                                                   |
                             +---------------------+---------------------+
                             |                                           |
                             v                                           v
                data/gold_layer/all_data.csv                 data/gold_layer/price_year.csv
                             |                                           |
                             +---------------------+---------------------+
                                                   |
                                                   v
                                        etl/load_mongodb.py
                                                   |
                                                   v
                           MongoDB `urban_data_explorer.metrics_yearly`
                                                   |
                              +--------------------+--------------------+
                              |                                         |
                              v                                         v
                 CsvDataStore (par défaut)                 MongoDataStore (optionnel)
                              \____________________  ____________________/
                                                   v
                                      backend/app.py (Flask API)
                                                   |
                                                   v
                                 frontend (HTML/CSS/JS + MapLibre)
```

## 3. Couches de données

| Couche | Emplacement | Rôle |
|--------|-------------|------|
| Bronze | `data/bronze_layer/` | Données brutes source : DVF, INSEE, qualité de l'air, géographie. |
| Silver | `data/silver_layer/` | Jeux nettoyés et harmonisés, prêts pour l'agrégation. |
| Gold | `data/gold_layer/all_data.csv`, `data/gold_layer/price_year.csv` | Jeux agrégés utilisés pour servir le dashboard. |
| Read model NoSQL | MongoDB `metrics_yearly` | Projection documentaire de la `gold`, optimisée pour la lecture applicative. |

### Position du NoSQL

MongoDB n'est pas utilisé comme couche `bronze`, `silver` ou `gold`.

Il est placé **après la gold**, dans une couche de **serving / lecture applicative** :

- la `gold` reste la source agrégée produite par l'ETL
- `etl/load_mongodb.py` transforme cette `gold` en documents MongoDB
- l'API Flask peut ensuite lire ces documents à la place des CSV

C'est ce choix qui évite de dupliquer toute la logique métier de nettoyage et d'agrégation dans MongoDB.

## 4. Flux de traitement

### 4.1 ETL

- `etl/clean.py` nettoie les données brutes et produit les fichiers `silver`
- `etl/aggregate.py` calcule les agrégats métier et produit :
  - `data/gold_layer/all_data.csv`
  - `data/gold_layer/price_year.csv`

### 4.2 Chargement MongoDB

- `etl/load_mongodb.py` lit les fichiers `gold`
- chaque document représente un couple `(code_commune, year)`
- le script génère aussi les documents `code_commune = "all"` pour Paris global
- un index unique est créé sur `(code_commune, year)`

### 4.3 Serving API

Le backend choisit sa source avec `UDE_DATA_BACKEND` :

- `csv` : lecture directe des fichiers `gold`
- `mongodb` : lecture de la collection `metrics_yearly`

## 5. Backend

Le backend principal est [backend/app.py](backend/app.py).

### 5.1 Rôle

- exposer les endpoints REST consommés par le frontend
- normaliser les paramètres fonctionnels, notamment les arrondissements
- retourner un format JSON stable pour les KPI, les courbes et les répartitions
- basculer entre backend `csv` et backend `mongodb`

### 5.2 Stores de données

Deux implémentations coexistent :

- `CsvDataStore`
  - charge `all_data.csv` et `price_year.csv`
  - calcule les métriques `Paris (all)` en mémoire
- `MongoDataStore`
  - lit les documents de la collection MongoDB
  - récupère directement les métriques par arrondissement et par année

Le choix se fait via :

```bash
UDE_DATA_BACKEND=csv
UDE_DATA_BACKEND=mongodb
```

Variables associées :

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=urban_data_explorer
MONGODB_COLLECTION=metrics_yearly
```

### 5.3 Endpoints principaux

- `/api/price`
- `/api/price/history`
- `/api/metrics`
- `/api/typology`
- `/api/surfaces`
- `/api/arrondissements`
- `/api/arrondissements.geojson`
- `/api/docs`
- `/api/docs.json`

## 6. Frontend

Le frontend est statique et vit dans :

- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`

### Responsabilités

- afficher la carte des arrondissements via MapLibre
- charger les KPI depuis l'API
- afficher les graphes de typologie, surface et historique de prix
- permettre une comparaison A/B entre arrondissements

### Dépendance API

Le frontend consomme les routes Flask pour toutes les données dynamiques.

En pratique :

- la carte charge `arrondissements.geojson`
- les KPI chargent `/api/metrics`
- les graphes chargent `/api/typology`, `/api/surfaces` et `/api/price/history`

## 7. Sécurité et performance

### Sécurité

- authentification JWT optionnelle via `UDE_REQUIRE_AUTH=1`
- secret applicatif configuré par `UDE_API_SECRET`
- validation des paramètres côté backend

### Performance

- mode `csv` :
  - très simple à démarrer
  - adapté au POC et aux faibles volumes
  - dépend d'un chargement mémoire au démarrage
- mode `mongodb` :
  - mieux adapté à une lecture applicative persistante
  - permet de découpler l'API de la lecture directe des fichiers
  - prépare le projet à une montée en charge ou à des enrichissements futurs

## 8. Pourquoi cette architecture

Cette architecture garde l'ETL lisible et reproductible, tout en ajoutant une couche NoSQL utile sans casser l'existant.

Le choix MongoDB a été fait pour trois raisons :

- les données du dashboard sont déjà agrégées et se prêtent bien à un modèle documentaire
- l'API lit surtout des objets par `(code_commune, year)`, ce qui correspond bien à MongoDB
- le backend peut évoluer vers une base de lecture sans refondre les pipelines `bronze/silver/gold`

## 9. Limites actuelles

- le frontend dépend encore d'une URL API locale
- la `gold` CSV reste la source de vérité de l'agrégation
- MongoDB est un read model, pas un moteur de transformation métier
- l'architecture ne gère pas encore l'orchestration planifiée de l'ETL

## 10. Pistes d'évolution

- scheduler ETL avec Airflow ou Prefect
- externaliser davantage la configuration applicative
- rendre l'URL API frontend configurable
- ajouter des tests d'intégration `csv` et `mongodb`
- étudier PostgreSQL/PostGIS si les besoins analytiques et géospatiaux deviennent plus complexes
