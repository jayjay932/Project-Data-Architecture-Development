# PROJET 1 — ARCHITECTURE DE DONNÉES
## Urban Data Explorer — Bloc 1 — Support de soutenance détaillé par compétence

---

## 0. INTRODUCTION RAPIDE (avant le détail par compétence)

### Besoin métier
Construire une plateforme data permettant d'explorer, comparer et comprendre les
dynamiques du logement à Paris, en croisant plusieurs sources publiques hétérogènes
(DVF, RATP, Airparif, INSEE, FiLoSoFi, APUR) dans une architecture robuste, sécurisée
et évolutive.

### Vue d'ensemble de l'architecture

```
SOURCES VARIÉES (CSV, XLSX, JSON)
        │
        ▼
  DATA LAKE (HDFS) — Bronze / Silver / Gold
        │
   ┌────┴────┐
   ▼         ▼
PostgreSQL  MongoDB
   │         │
   └────┬────┘
        ▼
   API REST Flask (MVC)
        │
        ▼
  Dashboard Web (MapLibre)
```

Toute l'infrastructure tourne en conteneurs Docker (12 services), orchestrés par
un unique `docker-compose.yml`.

---

## BLOC C1.1 — CONCEPTION ET DÉVELOPPEMENT D'UNE BASE RELATIONNELLE ADAPTÉE AU BESOIN

### Ce que la compétence attend
Démontrer la capacité à choisir, concevoir et peupler une base de données
relationnelle (SQL) cohérente avec la nature des données et les besoins d'accès.

### Notre solution
**PostgreSQL 16**, déployé en conteneur Docker (`postgres-paris`, port 5433),
hébergeant une base `urban_data_explorer` avec une table principale
`arrondissements` (20 lignes × 182 colonnes).

**Schéma de la table (extrait) :**
```sql
arrondissement          INTEGER PRIMARY KEY
prix_m2_median_2020...2025   NUMERIC
nb_ventes_2020...2025        INTEGER
population_2022              INTEGER
nb_menages_2022               INTEGER
revenu_median                 NUMERIC
indice_accessibilite          NUMERIC
indice_tension_sociale        NUMERIC
indice_attractivite           NUMERIC
indice_pression_immo          NUMERIC
... (182 colonnes au total)
```

### Pourquoi PostgreSQL et pourquoi une table unique ?
- Les données sont **stables dans leur structure** : chaque arrondissement a
  toujours les mêmes attributs (prix, évolutions, démographie) → le modèle
  relationnel à schéma fixe est parfaitement adapté, pas besoin de NoSQL ici.
- **PostgreSQL plutôt que MySQL** : support natif et mature du type JSON
  (extensibilité future), meilleure conformité SQL standard, outillage riche
  (pgAdmin), largement utilisé en production en entreprise.
- **Une seule table dénormalisée plutôt que plusieurs tables jointes** : avec
  seulement 20 lignes (un arrondissement = une ligne), la normalisation
  classique (3NF) aurait ajouté de la complexité de jointure sans bénéfice
  réel de performance ou d'intégrité — choix pragmatique justifié par le
  volume et l'usage (lecture analytique, pas transactionnelle).
- **Clé primaire sur `arrondissement`** : garantit l'unicité et accélère les
  requêtes de type `WHERE arrondissement = X`, qui sont le cas d'usage principal
  de l'API (fiche détail par arrondissement).

### Preuve technique
```bash
docker exec -it postgres-paris psql -U paris_admin -d urban_data_explorer
urban_data_explorer=# \dt
                List of relations
 Schema |       Name        | Type  |    Owner
--------+--------------------+-------+-------------
 public | arrondissements    | table | paris_admin

urban_data_explorer=# SELECT COUNT(*) FROM arrondissements;
 count
-------
    20

urban_data_explorer=# SELECT arrondissement, prix_m2_median_2024, revenu_median
                       FROM arrondissements ORDER BY prix_m2_median_2024 DESC LIMIT 3;
 arrondissement | prix_m2_median_2024 | revenu_median
----------------+----------------------+---------------
              6 |               14981  |        46350
              7 |               14620  |        51255
              1 |               12586  |        40750
```

### Limites
- Pas de normalisation poussée (table unique large) — choix assumé pour ce volume,
  à revoir si le projet passait à l'échelle de toute la France (plusieurs millions
  de lignes de transactions individuelles).
- Mot de passe en variable d'environnement claire dans le compose — acceptable en
  développement local, à externaliser via un secret manager en production.

---

## BLOC C1.2 — CONCEPTION ET DÉVELOPPEMENT D'UNE BASE NON RELATIONNELLE ADAPTÉE

### Ce que la compétence attend
Justifier l'usage du NoSQL pour des données dont la structure ne se prête pas
naturellement au modèle relationnel, et le démontrer techniquement.

### Notre solution
**MongoDB 7**, déployé en conteneur (`mongo-paris`, port 27017), avec 3 collections
dans la base `urban_data_explorer` :

| Collection | Documents | Structure |
|---|---|---|
| `transport_details` | 20 | Imbriquée, taille variable (`lignes`: 3 à 12 éléments selon arrondissement) |
| `typologie_historique` | 20 | Imbriquée sur 2 niveaux (année → type de logement → {nombre, pourcentage}) |
| `indicateurs_detail` | 20 | Imbriquée avec tableau de sources par indicateur |

**Exemple de document `transport_details` (arrondissement 8, riche en transport) :**
```json
{
  "arrondissement": 8,
  "metro": {
    "nb_stations": 15,
    "trafic_annuel": 72710440,
    "lignes": ["1","2","3","6","8","9","12","13","14","3bis"]
  },
  "rer": { "nb_lignes": 0, "lignes": [] }
}
```

**Même collection, arrondissement 5 (peu de transport) :**
```json
{
  "arrondissement": 5,
  "metro": {
    "nb_stations": 5,
    "trafic_annuel": 10301086,
    "lignes": ["4","7","10"]
  },
  "rer": { "nb_lignes": 1, "lignes": ["B"] }
}
```

### Pourquoi MongoDB plutôt que rester en SQL pour ces données ?
- **Structure intrinsèquement variable** : le nombre de lignes de métro par
  arrondissement varie de 0 à 10. En SQL, il faudrait soit créer des colonnes
  `ligne_1, ligne_2, ... ligne_12` majoritairement vides, soit une table de
  jointure séparée (`arrondissement_id, ligne`) — plus complexe à interroger
  pour un usage de type "donne-moi toutes les lignes de cet arrondissement".
- **Données imbriquées naturellement hiérarchiques** : `typologie_historique`
  a une structure année → type → {nombre, pourcentage} sur 6 ans × 5 types =
  30 sous-documents par arrondissement. Le modèle documentaire MongoDB stocke
  cette hiérarchie nativement en un seul document, alors que le SQL demanderait
  une table à 3 colonnes (année, type, valeur) avec 600 lignes au total — plus
  lourd à requêter pour reconstruire la vue par arrondissement.
- **Lecture optimisée pour l'usage cible** : l'API a besoin de "toutes les infos
  transport d'un arrondissement" en une seule requête — MongoDB répond avec
  `findOne({arrondissement: X})` sans JOIN.

### Preuve technique
```javascript
docker exec -it mongo-paris mongosh -u paris_admin -p paris2024 --authenticationDatabase admin
use urban_data_explorer
db.transport_details.countDocuments()          // → 20
db.typologie_historique.countDocuments()        // → 20
db.indicateurs_detail.countDocuments()          // → 20

db.transport_details.findOne({arrondissement: 8})
// → 10 lignes de métro (structure riche)
db.transport_details.findOne({arrondissement: 5})
// → 3 lignes de métro (même collection, structure différente)
```

### Limites
- Pas de validation de schéma stricte activée (MongoDB le permet via JSON Schema
  validators) — à ajouter pour renforcer la qualité des données en production.
- Duplication partielle de certaines données entre PostgreSQL et MongoDB
  (ex: `nb_lignes_metro` existe dans les deux) — choix pragmatique pour ce
  projet, à arbitrer plus strictement (source de vérité unique) à plus grande échelle.

---

## BLOC C1.3 — CONSTRUCTION D'UN DATA LAKE SÉCURISÉ INTÉGRANT DES SOURCES VARIÉES

### Ce que la compétence attend
Démontrer un stockage centralisé, traçable, sécurisé, capable d'ingérer des
formats de données hétérogènes, organisé en couches de maturité.

### Notre solution
**Deux briques complémentaires :**

1. **HDFS** (Hadoop Distributed File System) — cluster `namenode` + `datanode`,
   organisé en 3 couches :
   - `/datalake/bronze/` : données brutes post-ingestion (Parquet)
   - `/datalake/silver/` : données jointes/nettoyées
   - `/datalake/gold/` : agrégats finaux

2. **MinIO** — stockage objet compatible S3 (`minio-paris`, ports 9000/9001),
   pour les fichiers sources bruts multi-formats avant traitement.

### Sources variées intégrées
| Source | Format | Donnée |
|---|---|---|
| DVF (data.gouv.fr) | CSV (×6 années) | Transactions immobilières |
| RATP Open Data | CSV | Trafic et lignes par station |
| Airparif | CSV | Qualité de l'air |
| INSEE RP 2022 | XLSX | Démographie |
| FiLoSoFi (INSEE) | XLSX | Revenus médians |
| MongoDB (export) | JSON | Données transport semi-structurées |

### Pourquoi un Data Lake en plus des bases de données ?
- Les bases (Postgres/Mongo) ne contiennent que les données **finales,
  transformées**. Le Data Lake conserve les **données brutes et les étapes
  intermédiaires** — essentiel pour :
  - **Traçabilité** : pouvoir remonter à la donnée source en cas de doute
  - **Rejouabilité** : si une erreur est découverte dans le Gold, on peut
    relancer le pipeline depuis le Bronze sans re-télécharger les sources
  - **Auditabilité** : preuve de ce qui a été ingéré, quand, depuis où
- **HDFS plutôt qu'un simple dossier réseau** : réplication des blocs de
  données, conçu pour la tolérance de panne et la montée en charge horizontale
  (ajout de datanodes).
- **MinIO en complément** : interface S3 standard (portable vers le cloud
  AWS/OVH/Scaleway sans réécriture), avec authentification par clé d'accès.

### Sécurité mise en œuvre
- **HDFS** : accès via le réseau Docker interne uniquement (`namenode:9000`),
  pas d'exposition publique du port de données
- **MinIO** : authentification obligatoire par `MINIO_ROOT_USER` /
  `MINIO_ROOT_PASSWORD`, aucun accès anonyme aux buckets
- **Aucune donnée en clair accessible sans authentification** sur l'ensemble
  de la chaîne de stockage

### Preuve technique
```bash
# Interface web HDFS
http://localhost:9870/explorer.html#/datalake
# → arborescence bronze/ silver/ gold/ visible avec tailles de fichiers

# Vérification en ligne de commande
docker exec namenode hdfs dfs -ls /datalake/bronze/
docker exec namenode hdfs dfs -ls /datalake/silver/
docker exec namenode hdfs dfs -ls /datalake/gold/

# Résultat du pipeline d'ingestion :
[1/4] Ingestion des sources variées (CSV + JSON) → Bronze HDFS...
  ✓ CSV chargé : 20 lignes, 182 colonnes
  ✓ JSON chargé : 20 documents
  ✓ Écrit dans HDFS : /datalake/bronze/ (durée : 60.55s)
```

### Limites
- **Facteur de réplication = 1** (un seul datanode) — en production on viserait
  un facteur 3 sur plusieurs machines physiques pour une vraie tolérance de panne.
- Le volume actuel (quelques Mo) ne nécessite pas réellement HDFS — choix fait
  pour **démontrer la maîtrise** de l'outil en anticipation d'une montée en
  charge (passage à l'échelle nationale), pas par nécessité actuelle.

---

## BLOC C1.4 — ARCHITECTURE SCALABLE ET RÉSILIENTE

### Ce que la compétence attend
Prouver que l'architecture peut absorber une charge croissante et résister à
des pannes partielles sans interruption totale de service.

### Notre solution — mécanismes de résilience mis en place

**1. Conteneurisation avec redémarrage automatique**
```yaml
restart: unless-stopped
```
appliqué à tous les services critiques (postgres, mongo, minio, hadoop, spark)
→ un conteneur qui crashe redémarre automatiquement sans intervention manuelle.

**2. Healthchecks actifs**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U paris_admin -d urban_data_explorer"]
  interval: 5s
  timeout: 5s
  retries: 5
```
Docker surveille en continu l'état réel de PostgreSQL et MinIO (pas juste si
le process tourne, mais s'il répond correctement) — permet une détection
de panne applicative, pas seulement système.

**3. Scalabilité horizontale du cluster Spark**
Le cluster est conçu pour ajouter des workers sans changer le code applicatif :
```bash
docker-compose up -d --scale spark-worker-1=3
```
Le traitement distribué se répartirait automatiquement sur les workers
supplémentaires (le code utilise déjà `df.repartition(N)`, indépendant du
nombre de workers physiques).

**4. Réplication HDFS (capacité native)**
HDFS réplique nativement les blocs de données sur plusieurs datanodes — notre
cluster utilise 1 datanode pour la démo, mais l'ajout de `datanode-2`,
`datanode-3` dans le compose suffit à activer la réplication réelle sans
changement de code.

**5. Découplage des couches**
L'API ne dépend d'aucun fichier local — elle interroge uniquement PostgreSQL
et MongoDB. Si le Data Lake HDFS tombe, le dashboard reste fonctionnel
(seule l'ingestion de nouvelles données serait impactée, pas la consultation).

### Pourquoi ces choix plutôt que d'autres ?
- **Docker plutôt qu'installation native** : portabilité totale, démarrage
  identique sur n'importe quelle machine (`docker-compose up -d`), pas de
  dépendance à la configuration système de l'hôte.
- **Architecture en couches découplées** (Data Lake ≠ Bases ≠ API ≠ Frontend) :
  chaque couche peut tomber, redémarrer ou évoluer indépendamment sans
  réécrire les autres.

### Preuve technique
```bash
docker ps
# → tous les conteneurs "healthy" ou "Up"

# Test de résilience réel effectué pendant le développement :
docker stop postgres-paris
# → relancé automatiquement par restart policy après quelques secondes
docker ps  # postgres-paris de nouveau "Up"
```

### Limites
- Un seul hôte Docker (pas de cluster Docker Swarm/Kubernetes multi-machines)
  — la résilience démontrée est au niveau conteneur, pas au niveau matériel
  physique. Une vraie haute disponibilité demanderait plusieurs serveurs.
- Pas de load balancer devant l'API Flask (un seul process `app.py`) — en
  production, on ajouterait un reverse proxy (Nginx) + plusieurs instances API.

---

## BLOC C2.1 — CRÉATION D'UNE API INTEROPÉRABLE ET SÉCURISÉE

### Ce que la compétence attend
Démontrer une API suivant les standards REST, facilement consommable par
d'autres systèmes, avec des mécanismes de protection appropriés.

### Notre solution
**API Flask** suivant une architecture **MVC** stricte :
```
backend/
├── models/          → logique métier (classe Arrondissement)
├── controllers/      → endpoints (blueprints Flask)
├── services/          → accès aux données (DataLoader → PostgreSQL)
├── views/              → formatage des réponses JSON
└── middleware/        → gestion centralisée des erreurs, CORS
```

**Exemples d'endpoints filtrables :**
```
GET /api/prix/m2/<arrondissement>?annee=2024
GET /api/prix/comparaison?arrondissements=1,2,3&annee=2024
GET /api/logements/typologie/<arrondissement>?annee=2024
GET /api/transport/classement?critere=nb_lignes_metro
GET /api/pollution/polluant/no2?ordre=desc
```

### Pourquoi cette architecture et ces choix ?
- **Interopérabilité** : format de réponse JSON standardisé pour tous les
  endpoints :
  ```json
  {"success": true, "data": {...}, "timestamp": "2026-06-19T..."}
  ```
  Permet à n'importe quel client (web, mobile, autre service) de consommer
  l'API de façon prévisible.
- **MVC plutôt que tout dans un seul fichier** : séparation des responsabilités
  → maintenabilité, testabilité, et possibilité d'ajouter de nouveaux
  endpoints sans toucher au reste.
- **Endpoints filtrables par query params** : évite de multiplier les routes
  rigides, l'API reste flexible pour différents besoins du frontend (filtrage
  par année, comparaison multi-arrondissements).

### Sécurité mise en œuvre
- **CORS configuré** (`flask-cors`) pour contrôler quelles origines peuvent
  appeler l'API
- **Gestion d'erreurs centralisée** (`middleware/error_handler.py`) : aucune
  trace technique (stack trace Python) n'est jamais exposée au client, les
  erreurs 400/404/500 sont formatées proprement
- **Validation des entrées** sur chaque endpoint (vérification des bornes
  `1 <= arrondissement <= 20`, années valides, formats de paramètres)

### Preuve technique
```bash
curl http://localhost:5000/api/health
# {"success":true,"data":{"status":"healthy","nb_arrondissements":20}}

curl http://localhost:5000/api/arrondissements/25
# {"success":false,"error":{"message":"Numéro d'arrondissement invalide : 25"}}
# → validation des entrées fonctionnelle, pas de crash serveur

curl "http://localhost:5000/api/prix/comparaison?arrondissements=1,7,19&annee=2024"
# → comparaison filtrée fonctionnelle
```

### Limites
- Pas d'authentification par token (JWT/API Key) actuellement — tous les
  endpoints sont publics. Acceptable pour un dashboard de données publiques,
  mais à ajouter si l'API devait exposer des données sensibles ou être
  facturée à l'usage.
- Pas de limitation de débit (rate limiting) — à ajouter avant une mise en
  production réelle pour éviter les abus.

---

## BLOC C2.2 — MISE EN ŒUVRE D'UN SYSTÈME DISTRIBUÉ OU DE STREAMING

### Ce que la compétence attend
Démontrer un traitement de données réellement réparti sur plusieurs nœuds de
calcul (pas juste un seul process séquentiel).

### Notre solution
**Cluster Apache Spark** : 1 master + 2 workers, déployés en conteneurs Docker
distincts, communiquant sur le réseau Docker interne.

```
spark-master   (orchestrateur, port UI 8090)
   ├── spark-worker-1  (2 cores, 1 Go RAM)
   └── spark-worker-2  (2 cores, 1 Go RAM)
```

**Pipeline distribué exécuté (`pipeline_distribue.py`) :**
1. Lecture de 2 sources (CSV PostgreSQL-export + JSON MongoDB-export)
2. **Repartitionnement explicite** des données sur 4 partitions
   (`df.repartition(4)`) pour forcer la répartition du travail
3. Jointure entre les deux sources, exécutée en parallèle sur les workers
4. Agrégation distribuée (moyenne, somme) sur l'ensemble des 20 arrondissements

### Pourquoi Spark plutôt qu'un simple script Pandas séquentiel ?
- **Démonstration explicite du distribué** : Pandas/Python classique exécute
  tout sur un seul cœur, un seul process. Spark répartit réellement les
  partitions de données entre les workers et les traite en parallèle —
  c'est la différence fondamentale demandée par la compétence.
- **Pourquoi pas Kafka (streaming) ?** Choix assumé : Kafka répond à un besoin
  d'ingestion en flux continu (nouvelles données en temps réel), alors que
  notre cas d'usage est du traitement par lot (les données DVF sont publiées
  annuellement, pas en flux). Mettre en place Kafka aurait ajouté un risque
  technique important (complexité de configuration multi-conteneurs) sans
  bénéfice réel pour ce cas d'usage — préférence pour une solution distribuée
  robuste (Spark) plutôt qu'une solution streaming sur-dimensionnée.

### Preuve technique
```
http://localhost:8090  (UI Spark Master)
Alive Workers: 2
Cores in use: 4 Total, 0 Used
worker-1 : 172.26.0.12:39263 — ALIVE — 2 cores
worker-2 : 172.26.0.13:41199 — ALIVE — 2 cores
```

Log d'exécution réel :
```
26/06/19 11:13:37 INFO StandaloneAppClient: Executor added: .../0 on worker-...-172.26.0.12
26/06/19 11:13:37 INFO StandaloneAppClient: Executor added: .../1 on worker-...-172.26.0.13
26/06/19 11:13:42 INFO StandaloneAppClient: Executor updated: .../0 is now RUNNING
26/06/19 11:13:42 INFO StandaloneAppClient: Executor updated: .../1 is now RUNNING
...
[2/4] Transformation distribuée → Silver HDFS...
  ✓ Jointure CSV+JSON effectuée (durée : 5.89s)
  ✓ Nombre de partitions utilisées : 4
```
→ Les 2 executors sont actifs et participent à l'exécution (visible dans les
logs Spark : `Executor added` sur les 2 adresses IP distinctes des workers).

### Limites
- 2 workers seulement, sur la même machine hôte (pas de vrai cluster multi-
  machines physiques) — démontre le principe et la mécanique du distribué,
  pas un gain de performance réel à ce volume de données (20 lignes).
- Pas de mécanisme de streaming temps réel (choix assumé, voir justification
  ci-dessus) — à ajouter avec Kafka si le besoin métier évoluait vers de
  l'ingestion continue.

---

## BLOC C2.3 — TRANSFORMATION ET INTÉGRATION DE DONNÉES MULTI-SOURCES

### Ce que la compétence attend
Démontrer la capacité à fusionner des sources hétérogènes (formats, structures,
granularités différentes) en un jeu de données cohérent et exploitable.

### Notre solution — 6 sources fusionnées

| Source | Format | Granularité initiale | Transformation appliquée |
|---|---|---|---|
| DVF | CSV (×6 fichiers annuels) | Transaction individuelle | Agrégation par arrondissement × année (médiane prix/m²) |
| RATP | CSV | Station de métro | Agrégation par arrondissement (somme trafic, liste lignes dédupliquées) |
| Airparif | CSV | Mesure ponctuelle | Moyenne par arrondissement |
| INSEE RP 2022 | Référentiel fixe (dict Python) | Commune/arrondissement | Jointure directe sur code arrondissement |
| FiLoSoFi | XLSX | IRIS (sous-quartier) | Agrégation par médiane des IRIS → arrondissement |
| APUR | Référentiel fixe | Arrondissement | Jointure directe |

### Défis techniques rencontrés et résolus
1. **Granularités différentes** : DVF est au niveau transaction, FiLoSoFi au
   niveau IRIS (plus fin que l'arrondissement), RATP au niveau station — il a
   fallu agréger chaque source à la granularité commune (l'arrondissement)
   avant de pouvoir les joindre.
2. **Formats de clé incohérents** : codes postaux (`75001`), codes INSEE
   (`75101`), numéros simples (`1`) selon les sources — normalisation
   systématique vers un entier `1-20` via des fonctions d'extraction dédiées
   (`extraire_arrondissement_insee()`, `extraire_arrondissement_nom()`).
3. **Doublons et incohérences** : les lignes de métro contenaient des doublons
   liés à un artefact de typage (`"14"` et `"14.0"` pour la même ligne) —
   détectés et corrigés par un script de nettoyage dédié.
4. **Données manquantes par construction** : `population_2018` était
   identique pour les 20 arrondissements dans une première version (donnée
   source mal jointe, total Paris dupliqué) — détecté, corrigé en réinjectant
   les vraies valeurs INSEE 2022 par arrondissement.

### Pourquoi cette approche de fusion (Python/Pandas) ?
- Permet un contrôle fin de chaque étape de transformation, avec logs
  explicites à chaque source ingérée (traçabilité)
- Architecture en script unique reproductible (`dashboard_final.py`),
  exécutable de bout en bout pour régénérer le Gold à tout moment

### Preuve technique
```python
# Extrait du pipeline de fusion (dashboard_final.py)
gold["population_2022"] = gold["arrondissement"].map(POPULATION_2022)
gold["revenu_median"] = gold["arrondissement"].map(revenus_par_arr)
# → jointure de 6 sources distinctes sur la clé commune 'arrondissement'

# Résultat : 182 colonnes dans une table unique
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'arrondissements';
# → 182
```

### Limites
- Les référentiels démographiques (population, logements sociaux) sont
  actuellement des dictionnaires Python statiques plutôt que rechargés
  dynamiquement depuis une API INSEE — à industrialiser pour des mises à jour
  automatiques.
- Pas de gestion de versions du schéma Gold (si une source change de format,
  le pipeline doit être ajusté manuellement).

---

## BLOC C2.4 — OPTIMISATION DES PIPELINES ET MESURE DE LA PERFORMANCE

### Ce que la compétence attend
Démontrer une démarche de mesure objective de la performance et des choix
techniques visant à l'optimiser.

### Notre solution — mesures réalisées

**1. Mesure du pipeline distribué Spark (par étape) :**
| Étape | Durée mesurée | Volume traité |
|---|---|---|
| Ingestion CSV+JSON → Bronze HDFS | 60,55 s | 20 lignes × 182 col + 20 docs JSON |
| Jointure distribuée → Silver HDFS | 5,89 s | Jointure sur 4 partitions |
| Agrégation distribuée → Gold HDFS | 7,85 s | Agrégats sur 20 arrondissements |
| **Total pipeline** | **~74 s** | |

**2. Choix de format optimisé : Parquet plutôt que CSV dans HDFS**
- Parquet est un format **colonnaire et compressé** : pour des requêtes
  analytiques (moyennes, sommes par colonne), il est largement plus
  performant que le CSV en lecture, car seules les colonnes nécessaires
  sont lues (pas le fichier entier ligne par ligne).

**3. Optimisation de l'accès API : SQL direct plutôt que chargement complet**
Comparaison des deux approches dans `data_loader.py` :
```python
# AVANT (CSV) : chargement de tout le fichier à chaque requête
df = pd.read_csv(GOLD_CSV)              # relit 182 colonnes × 20 lignes
row = df[df['Arrondissement'] == numero] # puis filtre en mémoire

# APRÈS (PostgreSQL) : requête ciblée
SELECT * FROM arrondissements WHERE arrondissement = :numero
# → l'index de clé primaire est utilisé directement par PostgreSQL
```
La requête SQL ciblée évite de charger les 182 colonnes × 20 lignes en mémoire
Python à chaque appel API — le filtrage est délégué au moteur de base de
données, optimisé pour cela.

**4. Repartitionnement explicite pour exploiter le cluster**
```python
df_gold_repartitioned = df_gold.repartition(4)
```
Sans cette ligne, Spark aurait pu traiter les données sur une seule partition
(un seul worker actif, l'autre inutilisé). Le repartitionnement force
l'exploitation des 2 workers disponibles.

### Pourquoi mesurer plutôt que simplement affirmer la performance ?
- Une architecture distribuée mal utilisée (sans repartitionnement, par
  exemple) peut être **plus lente** qu'un script séquentiel sur un petit
  volume — la mesure permet de vérifier que les choix techniques sont
  réellement justifiés et pas seulement "à la mode".

### Preuve technique
```
[1/4] Ingestion des sources variées (CSV + JSON) → Bronze HDFS...
  ✓ Écrit dans HDFS : /datalake/bronze/ (durée : 60.55s)
[2/4] Transformation distribuée → Silver HDFS...
  ✓ Nombre de partitions utilisées : 4
  ✓ durée : 5.89s
[3/4] Agrégation distribuée sur le cluster → Gold HDFS...
  ✓ durée : 7.85s
```

### Limites
- Le volume de données actuel (20 lignes) est trop faible pour observer un
  réel gain de performance du distribué par rapport à un traitement
  séquentiel — la démarche de mesure est en place, mais le bénéfice ne
  deviendrait visible qu'à plus grande échelle (milliers/millions de lignes).
- Pas de benchmark formalisé comparant explicitement Spark vs Pandas sur un
  même volume — amélioration possible : exécuter le même traitement en
  Pandas pur et chronométrer pour objectiver le gain (ou l'absence de gain
  à ce volume).

---

## SYNTHÈSE — TABLEAU RÉCAPITULATIF

| Compétence | Techno | Preuve clé | Statut |
|---|---|---|---|
| C1.1 | PostgreSQL | `SELECT COUNT(*)` → 20 lignes, 182 colonnes | ✅ |
| C1.2 | MongoDB | 3 collections, structures variables démontrées | ✅ |
| C1.3 | HDFS + MinIO | Bronze/Silver/Gold visibles, sources CSV+XLSX+JSON | ✅ |
| C1.4 | Docker + healthchecks | `restart: unless-stopped`, test de panne réussi | ✅ |
| C2.1 | Flask REST MVC | Endpoints filtrables, gestion d'erreurs, CORS | ✅ |
| C2.2 | Spark (2 workers) | UI Spark, jointure distribuée sur 4 partitions | ✅ |
| C2.3 | Pipeline Pandas | 6 sources fusionnées, 182 colonnes finales | ✅ |
| C2.4 | Mesures de temps | Temps par étape mesurés et affichés | ✅ |

---

## NOTES DE PRÉSENTATION ORALE (9 minutes)

| Temps | Bloc(s) | Message clé |
|---|---|---|
| 0:00–1:00 | Intro + architecture | Montrer le schéma global, poser le besoin métier |
| 1:00–2:30 | C1.1 + C1.2 | "Pourquoi deux bases ? Parce que deux natures de données différentes" |
| 2:30–4:00 | C1.3 + C1.4 | Montrer HDFS UI, expliquer Bronze/Silver/Gold, healthchecks |
| 4:00–6:00 | C2.1 + C2.2 | Montrer un appel API en direct, puis l'UI Spark avec 2 workers actifs |
| 6:00–7:30 | C2.3 + C2.4 | Expliquer les défis de fusion rencontrés, montrer les temps mesurés |
| 7:30–9:00 | Synthèse + limites | Tableau récapitulatif, assumer les limites sans se justifier excessivement |

**Conseil clé :** pour chaque bloc, suivre la structure *"Voici ce qu'on a fait →
voici pourquoi ce choix plutôt qu'un autre → voici la preuve que ça marche"*.
Le jury valorise la **justification du choix** bien plus que la liste des outils.










## Indicateurs composites calculés

Le fichier gold final contient plusieurs indicateurs composites permettant de comparer les arrondissements de Paris sur une échelle commune.
Ces indicateurs sont calculés à partir des données immobilières, démographiques, sociales et de transport agrégées par arrondissement.

### Principe de normalisation

Avant de calculer les indices, certaines variables sont normalisées sur une échelle de **0 à 10** afin de pouvoir comparer des grandeurs différentes entre elles.

La normalisation utilisée est une normalisation min-max :

```python
score = (valeur - minimum) / (maximum - minimum) * 10
```

Ainsi :

* `0` correspond à la valeur la plus faible observée parmi les 20 arrondissements ;
* `10` correspond à la valeur la plus forte observée ;
* les autres valeurs sont positionnées proportionnellement entre 0 et 10.

Dans certains cas, le score est inversé avec `inverse=True`.
Cela signifie qu’une valeur faible devient favorable.

Exemple :

```python
normaliser(ratio_effort_achat, inverse=True)
```

Dans ce cas, plus le ratio d’effort d’achat est faible, meilleur est le score d’accessibilité.

---

## 1. Ratio d’effort d’achat

Le `ratio_effort_achat` mesure le nombre d’années de revenu médian nécessaires pour acheter un logement de **50 m²** dans un arrondissement.

Formule :

```python
ratio_effort_achat = prix_m2_median_2024 * 50 / revenu_median
```

Interprétation :

* un ratio faible signifie que l’achat est plus accessible ;
* un ratio élevé signifie que l’achat est plus difficile.

Exemple :

```text
Prix au m² : 10 000 €
Surface cible : 50 m²
Prix estimé du bien : 500 000 €
Revenu médian : 25 000 €

Ratio effort achat = 500 000 / 25 000 = 20 ans
```

Ce ratio sert ensuite à calculer l’indice d’accessibilité.

---

## 2. Indice d’accessibilité

L’`indice_accessibilite` mesure la facilité d’accès à la propriété dans un arrondissement.

Il est calculé à partir du `ratio_effort_achat`, puis normalisé sur 10 avec inversion du score.

Formule :

```python
indice_accessibilite = normaliser(ratio_effort_achat, inverse=True)
```

Interprétation :

* `10` = arrondissement le plus accessible financièrement ;
* `0` = arrondissement le moins accessible ;
* plus le ratio d’effort d’achat est faible, plus l’indice est élevé.

Cet indice permet donc d’identifier les arrondissements où le prix immobilier est plus cohérent avec le niveau de revenu médian.

---

## 3. Indice de tension sociale

L’`indice_tension_sociale` mesure la pression sociale liée au marché immobilier.

Il combine deux dimensions :

* le niveau des prix immobiliers ;
* la part de logements sociaux.

Formule :

```python
indice_tension_sociale = (
    normaliser(prix_m2_median_2024)
    +
    normaliser(part_logements_sociaux_apur_pct, inverse=True)
) / 2
```

Logique de calcul :

* un prix au m² élevé augmente la tension sociale ;
* une faible part de logements sociaux augmente aussi la tension sociale.

Interprétation :

* `10` = forte tension sociale ;
* `0` = faible tension sociale.

Un arrondissement avec des prix élevés et peu de logements sociaux aura donc un score de tension sociale plus important.

---

## 4. Indice d’attractivité

L’`indice_attractivite` mesure l’attractivité urbaine d’un arrondissement.

Il repose sur trois variables :

* le trafic total du métro ;
* le nombre de lignes de métro ;
* le prix médian au m².

Formule :

```python
indice_attractivite = (
    normaliser(trafic_total_metro) * 0.4
    +
    normaliser(nb_lignes_metro) * 0.3
    +
    normaliser(prix_m2_median_2024) * 0.3
)
```

Pondération :

```text
40 % : trafic total métro
30 % : nombre de lignes métro
30 % : prix médian au m²
```

Interprétation :

* `10` = arrondissement très attractif ;
* `0` = arrondissement moins attractif selon les critères retenus.

L’idée est qu’un arrondissement bien desservi, très fréquenté et valorisé sur le marché immobilier est considéré comme plus attractif.

---

## 5. Indice de pression immobilière

L’`indice_pression_immo` mesure la pression ou l’activité du marché immobilier local.

Il combine trois variables :

* l’évolution du prix au m² entre 2023 et 2024 ;
* le nombre de ventes en 2024 ;
* la part de logements T1.

Formule :

```python
indice_pression_immo = (
    normaliser(evolution_prix_m2_2023_2024_pct, inverse=True) * 0.4
    +
    normaliser(nb_ventes_2024) * 0.3
    +
    normaliser(pct_T1_2024) * 0.3
)
```

Pondération :

```text
40 % : évolution du prix au m² 2023-2024, inversée
30 % : volume de ventes en 2024
30 % : part de T1
```

Dans cette logique, une pression immobilière élevée correspond à :

* un marché avec beaucoup de transactions ;
* une forte présence de petits logements ;
* une évolution des prix plus faible ou en baisse, ce qui peut signaler une zone active mais sous tension ou en réajustement.

Interprétation :

* `10` = forte pression immobilière ;
* `0` = pression immobilière plus faible.

---

## Résumé des indicateurs

| Indicateur               | Variables utilisées                   | Interprétation                                                  |
| ------------------------ | ------------------------------------- | --------------------------------------------------------------- |
| `ratio_effort_achat`     | Prix/m² 2024, revenu médian           | Nombre d’années de revenu nécessaires pour acheter 50 m²        |
| `indice_accessibilite`   | Ratio d’effort d’achat inversé        | Plus le score est élevé, plus l’achat est accessible            |
| `indice_tension_sociale` | Prix/m², part de logements sociaux    | Plus le score est élevé, plus la tension sociale est forte      |
| `indice_attractivite`    | Trafic métro, lignes métro, prix/m²   | Plus le score est élevé, plus l’arrondissement est attractif    |
| `indice_pression_immo`   | Évolution prix/m², ventes, part de T1 | Plus le score est élevé, plus la pression immobilière est forte |

---

## Remarque méthodologique

Les indices sont des indicateurs comparatifs construits à partir des données disponibles.
Ils ne donnent pas une vérité absolue, mais permettent de comparer les arrondissements entre eux selon une grille commune.

Les scores sont calculés uniquement à l’échelle des 20 arrondissements parisiens.
Un score élevé signifie donc que l’arrondissement se situe parmi les plus hauts de Paris sur les critères considérés.
