# Urban Data Explorer – Documentation

## Vue d’ensemble

Urban Data Explorer est une application full-stack permettant de visualiser l’évolution du marché immobilier parisien, ses indicateurs socio-économiques ainsi que la composition du parc résidentiel. Le projet se structure autour de trois briques principales :

1. **ETL (`etl/`)** – consolide les données brutes (DVF, socio-économie, qualité de l’air, densité) vers une table gold `data/gold_layer/all_data.csv`.
2. **Backend Flask (`backend/`)** – expose les métriques à l’application via des endpoints REST documentés par Swagger.
3. **Frontend statique (`frontend/`)** – interface HTML/CSS/JS (MapLibre + canvas custom) offrant diverses visualisations et comparatifs interactifs.

```
├── backend/
│   ├── app.py             # API Flask + Swagger
│   └── ...
├── etl/
│   ├── aggregate.py       # Pipeline d’agrégation vers gold layer
│   └── ...
├── data/
│   ├── bronze_layer/      # Données sources
│   ├── silver_layer/      # Données nettoyées
│   └── gold_layer/        # Données agrégées servies à l’API
└── frontend/
    ├── index.html         # UI tabs (Overview, Comparaison, Data)
    ├── app.js             # Logique de rendu (cartes, graphiques, tooltips…)
    └── style.css
```

## Pipeline de données

1. **Bronze ➜ Silver (`etl/clean.py`)**
   - Nettoyage: encodage, normalisation des codes INSEE, filtrage des surfaces aberrantes.
   - Calculs: prix/m², typologies via `nombre_pieces_principales`, surfaces INSEE, densité.

2. **Silver ➜ Gold (`etl/aggregate.py`)**
   - Agrégation par couple `(code_commune, annee)` :
     - Prix médian, variation vs année N-1.
     - Mix typologique (counts + parts).
     - Mix surface (<20, 20‑40, 40‑60, 60‑80, 80‑120, >120 m²).
     - Transactions, revenus, logements sociaux, qualité de l’air, densité.
   - Fusion avec indicateurs socio-économiques.
   - Export `data/gold_layer/all_data.csv`.

3. **City-level metrics** : `backend/app.py` produit `CITY_METRICS` en sommant l’ensemble des arrondissements pour les vues “Paris (all)”.

## API Backend

Serveur Flask (port 8000) avec CORS activé.

| Endpoint                     | Description                                      |
|-----------------------------|--------------------------------------------------|
| `GET /api/price?year=`      | Prix médian/m² global pour une année.            |
| `GET /api/price/history`    | Historique des prix (ville ou arrondissement).   |
| `GET /api/metrics`          | Métriques complètes (prix, revenus, densité…).   |
| `GET /api/typology`         | Répartition par typologie de logement.           |
| `GET /api/surfaces`         | Répartition du parc par classes de surface.      |
| `GET /api/arrondissements`  | Liste code/libellé des arrondissements.          |
| `GET /api/arrondissements.geojson` | Polygones GeoJSON pour MapLibre.         |
| `GET /api/docs`             | Swagger UI (doc interactive).                    |
| `GET /api/docs.json`        | Spécification OpenAPI brute.                     |

Tous les endpoints acceptent `arrondissement=all` pour l’agrégat ville. Les schémas de réponse sont décrits dans Swagger (définis dans `SWAGGER_SPEC`).

## Frontend

- **Tabs** : Vue d’ensemble (carte + KPIs + typologie + surfaces), Comparaison (cartes A/B, radar multi-axes, historique graphiques), Données.
- **MapLibre** : `frontend/app.js` initie la carte, survols et popups.
- **Graphiques canvas** :
  - Typologie donut + tooltips custom.
  - Bar chart surfaces aligné sur classes <20 → >120 m².
  - Line chart “Évolution du prix” filtre arrondissements & années.
  - Radar multi-axes comparant prix, logements sociaux, revenus, densité, transactions.

## Lancer le projet

1. **Installer les dépendances**  
   ```
   python -m venv venv
   source venv/bin/activate  # (ou venv\Scripts\activate sous Windows)
   pip install -r requirements.txt
   ```

2. **Générer les données gold (si besoin)**  
   ```
   ./venv/Scripts/python etl/aggregate.py
   ```

3. **Lancer l’API**  
   ```
   ./venv/Scripts/python backend/app.py
   ```
   Accéder ensuite à `http://localhost:8000` pour l’UI, `http://localhost:8000/api/docs` pour Swagger.

4. **Développement frontend** : Les fichiers statiques sont servis directement par Flask. Toute modification dans `frontend/` est automatiquement reflétée après rechargement du navigateur.

## Tests & vérifications rapides

```bash
# Vérifier qu’un endpoint répond
curl "http://localhost:8000/api/metrics?year=2024&arrondissement=75101"

# Consulter la doc interactive
open http://localhost:8000/api/docs
```

## Notes d’architecture

- Les graphiques utilisent des canvas purs (sans libs) pour garder un bundle léger.
- Cache côté frontend (`Map`, `priceHistoryCache`, etc.) pour éviter les re-fetchs.
- L’API valide systématiquement les codes INSEE via `normalize_arrondissement_code`.
- Swagger facilite l’onboarding des nouvelles intégrations (data scientists, BI, etc.).

Pour plus de détails, voir :
- `etl/aggregate.py` pour les transformations calculatoires.
- `frontend/app.js` (sections `renderTypologyChart`, `renderSurfaceChart`, `renderPriceTrendChart`, `renderComparisonRadar`).
- `backend/app.py` pour les points d’entrée API et la doc Swagger.
