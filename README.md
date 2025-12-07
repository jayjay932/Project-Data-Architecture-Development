# Urban Data Explorer

Urban Data Explorer est une application de dataviz qui aide les collectivités, investisseurs et citoyens à comprendre l’évolution du marché immobilier parisien (prix, typologies, surfaces, revenus, qualité de l’air, etc.). Le projet fournit :

- Un **frontend** responsive (MapLibre + graphiques canvas) avec onglets “Vue d’ensemble”, “Comparaison” et “Données”.
- Une **API Flask** documentée par Swagger (`/api/docs`) pour intégrer les métriques dans d’autres outils.
- Un **pipeline ETL** reproductible (`etl/`) qui consolide les données DVF et socio-économiques en un jeu de données “gold” prêt à l’emploi.

![Aperçu](spec/preview.png) <!-- facultatif si image disponible -->

## Fonctionnalités principales

- Carte interactive des prix/m² avec popups contextualisés.
- KPI dynamiques (prix, revenus, logements sociaux, densité, qualité de l’air).
- Graphiques dédiés : typologies, surfaces, évolution prix, radar comparatif multi-axes.
- Mode comparaison A/B avec filtres année/arrondissements et validation intégrée.
- Documentation Swagger et endpoints REST pour alimenter notebooks ou outils BI.

## Prérequis

- Python 3.11+
- Pip / virtualenv
- (optionnel) Node/npm pour outils tiers, mais le frontend est purement statique.

## Installation & démarrage rapide

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Générer ou mettre à jour les données gold
python etl/aggregate.py

# 4. Lancer l’API + frontend statique
python backend/app.py
```

L’application est accessible sur `http://localhost:8000`.  
La documentation interactive est publiée sur `http://localhost:8000/api/docs`.

## Consommation API rapide

```bash
# Prix médian 2024
curl "http://localhost:8000/api/price?year=2024"

# Métriques complètes pour le 6ᵉ arrondissement en 2023
curl "http://localhost:8000/api/metrics?year=2023&arrondissement=75106"

# Historique des prix pour Paris (all)
curl "http://localhost:8000/api/price/history?arrondissement=all"
```

Toutes les routes et schémas sont décrits dans Swagger.

## Structure du dépôt

```
backend/     # API Flask + doc Swagger
etl/         # Pipelines de nettoyage et d’agrégation
frontend/    # HTML/CSS/JS (MapLibre + graphiques custom)
data/        # Bronze / Silver / Gold
README.md    # Guide utilisateur (ce document)
architecture.md   # Documentation d’architecture détaillée
data_catalog.md   # Data catalog / justification des sources
```

## Ressources complémentaires

- [architecture.md](architecture.md) : description détaillée des couches de données, du backend et des interactions front/backend.
- [data_catalog.md](data_catalog.md) : mini data catalog expliquant les sources (DVF, INSEE, Airparif…), les champs exposés et les choix méthodologiques.
- [Swagger UI](http://localhost:8000/api/docs) : tester/explorer l’API.

## Support

En cas de question ou de bug :

1. Vérifier les logs du serveur (`backend/app.py`).
2. Confirmer que le pipeline ETL a bien généré `data/gold_layer/all_data.csv`.
3. Consulter la doc Swagger pour valider les paramètres.

Des contributions sont les bienvenues via issues/pull requests. Merci ! :)
