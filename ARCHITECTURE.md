# Architecture du Projet - Dashboard Immobilier Paris

## 📋 Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Justification de l'architecture MVC](#justification-de-larchitecture-mvc)
3. [Structure des dossiers](#structure-des-dossiers)
4. [Couche Data (Bronze/Silver/Gold)](#couche-data)
5. [Architecture API (Backend)](#architecture-api-backend)
6. [Architecture Frontend](#architecture-frontend)
7. [Flux de données](#flux-de-données)

---

## 🎯 Vue d'ensemble

Ce projet implémente un **dashboard immobilier interactif** pour les arrondissements de Paris, suivant le pattern **MVC (Model-View-Controller)** avec une séparation claire entre :
- **Data Pipeline** (Bronze → Silver → Gold)
- **Backend API** (Flask/FastAPI avec architecture MVC)
- **Frontend** (MapLibre + interface interactive)

---

## 🏗️ Justification de l'architecture MVC

### Pourquoi MVC ?

#### 1. **Séparation des responsabilités**
- **Model** : Gestion des données et logique métier
- **View** : Présentation et interface utilisateur
- **Controller** : Orchestration et logique applicative

#### 2. **Maintenabilité**
- Modifications isolées sans impact sur les autres couches
- Code plus lisible et testable
- Facilite le travail en équipe

#### 3. **Scalabilité**
- Ajout facile de nouveaux endpoints
- Extension du modèle de données sans refonte
- Évolution indépendante du frontend et backend

#### 4. **Réutilisabilité**
- Models réutilisables dans différents contextes
- Controllers modulaires et composables
- Views interchangeables

---

## 📁 Structure des dossiers

```
projet_data_architecture/
│
├── data/                           # 🗄️ COUCHE DATA (Pipeline ETL)
│   ├── bronze/                     # Données brutes (sources externes)
│   │   ├── dvf_2020.csv
│   │   ├── dvf_2021.csv
│   │   ├── ...
│   │   ├── trafic-annuel-entrant-par-station.csv
│   │   └── README.md              # Documentation des sources
│   │
│   ├── silver/                     # Données nettoyées et transformées
│   │   ├── 75_2020_clean.csv
│   │   ├── 75_2021_clean.csv
│   │   ├── ...
│   │   ├── air_quality_paris_final.csv
│   │   ├── stats_commune_2014_2020.csv
│   │   └── README.md              # Documentation des transformations
│   │
│   ├── gold/                       # Données agrégées et prêtes à l'emploi
│   │   ├── dashboard_arrondissements_paris7.csv
│   │   └── README.md              # Documentation du schéma final
│   │
│   └── processing/                 # Scripts de transformation
│       ├── 01_bronze_to_silver.py
│       ├── 02_silver_to_gold.py
│       └── utils/
│           ├── __init__.py
│           ├── data_cleaner.py
│           └── validators.py
│
├── backend/                        # 🔧 BACKEND API (MVC)
│   ├── app.py                      # Point d'entrée de l'application
│   ├── config.py                   # Configuration (DB, API keys, etc.)
│   ├── requirements.txt
│   │
│   ├── models/                     # 📊 MODELS (Couche métier)
│   │   ├── __init__.py
│   │   ├── base.py                # Classe de base pour les models
│   │   ├── arrondissement.py      # Model principal
│   │   ├── prix.py                # Logique prix/m²
│   │   ├── logement.py            # Typologie des logements
│   │   ├── transport.py           # Données transport
│   │   └── pollution.py           # Qualité de l'air
│   │
│   ├── controllers/                # 🎮 CONTROLLERS (Logique applicative)
│   │   ├── __init__.py
│   │   ├── prix_controller.py     # Endpoints prix/marché
│   │   ├── logement_controller.py # Endpoints logements sociaux
│   │   ├── typologie_controller.py # Endpoints typologie
│   │   ├── transport_controller.py # Endpoints transport
│   │   └── pollution_controller.py # Endpoints pollution
│   │
│   ├── services/                   # 🔄 SERVICES (Logique réutilisable)
│   │   ├── __init__.py
│   │   ├── data_loader.py         # Chargement CSV Gold
│   │   ├── calculator.py          # Calculs et statistiques
│   │   └── cache.py               # Gestion du cache
│   │
│   ├── views/                      # 📋 VIEWS (Sérialisation réponses)
│   │   ├── __init__.py
│   │   ├── response_formatter.py  # Format des réponses JSON
│   │   └── schemas.py             # Schémas Pydantic/Marshmallow
│   │
│   ├── middleware/                 # 🛡️ MIDDLEWARE
│   │   ├── __init__.py
│   │   ├── cors.py
│   │   ├── error_handler.py
│   │   └── logger.py
│   │
│   └── tests/                      # 🧪 TESTS
│       ├── test_models.py
│       ├── test_controllers.py
│       └── test_integration.py
│
├── frontend/                       # 🎨 FRONTEND
│   ├── index.html                  # Page principale
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── map.js             # Gestion carte MapLibre
│   │       ├── api.js             # Appels API
│   │       ├── ui.js              # Interface utilisateur
│   │       └── utils.js           # Utilitaires
│   │
│   └── components/                 # Composants réutilisables
│       ├── legend.js
│       ├── tooltip.js
│       └── filters.js
│
├── docs/                           # 📚 DOCUMENTATION
│   ├── API.md                      # Documentation API
│   ├── DATA_DICTIONARY.md          # Dictionnaire de données
│   └── DEPLOYMENT.md               # Guide de déploiement
│
└── README.md                       # Documentation principale
```

---

## 🗄️ Couche Data (Bronze/Silver/Gold)

### Principe de la Médaille (Bronze → Silver → Gold)

#### 🥉 **Bronze** : Données brutes
- **Objectif** : Stockage des données sources sans transformation
- **Format** : CSV, JSON bruts des sources externes
- **Exemples** :
  - `dvf_2020.csv` : Données DVF brutes
  - `trafic-annuel-entrant-par-station.csv` : Trafic métro brut

#### 🥈 **Silver** : Données nettoyées
- **Objectif** : Nettoyage, validation, normalisation
- **Transformations** :
  - Suppression des doublons
  - Correction des types de données
  - Normalisation des noms de colonnes
  - Filtrage des valeurs aberrantes
- **Exemples** :
  - `75_2020_clean.csv` : DVF nettoyé pour Paris 2020
  - `air_quality_paris_final.csv` : Qualité air normalisée

#### 🥇 **Gold** : Données agrégées
- **Objectif** : Données prêtes pour l'analyse et l'API
- **Transformations** :
  - Agrégation par arrondissement
  - Calcul des métriques dérivées
  - Jointure multi-sources
- **Sortie** : `dashboard_arrondissements_paris7.csv`

---

## 🔧 Architecture API (Backend)

### Structure MVC détaillée

#### 1. **MODELS** (`backend/models/`)

**Responsabilité** : Représentation et logique métier des données

##### `arrondissement.py`
```python
class Arrondissement:
    """Model principal représentant un arrondissement"""
    
    def __init__(self, numero: int, data: dict):
        self.numero = numero
        self._data = data
    
    @property
    def prix_m2_median_2024(self) -> Optional[float]:
        """Prix/m² médian en 2024"""
        return self._data.get('prix_m2_median_2024')
    
    def get_evolution_prix(self, annee_debut: int, annee_fin: int) -> float:
        """Calcule l'évolution des prix entre deux années"""
        # Logique métier
```

##### `prix.py`
```python
class PrixModel:
    """Logique métier pour les prix immobiliers"""
    
    @staticmethod
    def calculer_evolution(prix_debut, prix_fin) -> dict:
        """Calcule évolution en % et catégorie de tendance"""
        # Logique de calcul
```

##### `logement.py`
```python
class LogementModel:
    """Logique métier pour la typologie des logements"""
    
    def get_repartition_pieces(self, annee: int) -> dict:
        """Retourne la répartition T1/T2/T3/T4/T5+"""
```

---

#### 2. **CONTROLLERS** (`backend/controllers/`)

**Responsabilité** : Orchestration des requêtes HTTP et appels aux models

##### `prix_controller.py`
```python
from flask import Blueprint, jsonify, request
from models.arrondissement import Arrondissement
from services.data_loader import DataLoader
from views.response_formatter import format_response

prix_bp = Blueprint('prix', __name__, url_prefix='/api/prix')

@prix_bp.route('/m2/<int:arrondissement>', methods=['GET'])
def get_prix_m2(arrondissement: int):
    """
    GET /api/prix/m2/1?annee=2024
    Retourne le prix/m² médian pour un arrondissement
    """
    annee = request.args.get('annee', 2024, type=int)
    
    # Charge les données via le service
    arr_data = DataLoader.get_arrondissement(arrondissement)
    arr_model = Arrondissement(arrondissement, arr_data)
    
    # Récupère la métrique via le model
    prix_m2 = arr_model.get_prix_m2(annee)
    
    # Formate la réponse via la view
    return format_response({
        'arrondissement': arrondissement,
        'annee': annee,
        'prix_m2_median': prix_m2
    })

@prix_bp.route('/evolution', methods=['GET'])
def get_evolution_prix():
    """
    GET /api/prix/evolution?arrondissement=1&debut=2020&fin=2024
    Retourne l'évolution des prix
    """
    arrondissement = request.args.get('arrondissement', type=int)
    debut = request.args.get('debut', 2020, type=int)
    fin = request.args.get('fin', 2024, type=int)
    
    arr_data = DataLoader.get_arrondissement(arrondissement)
    arr_model = Arrondissement(arrondissement, arr_data)
    
    evolution = arr_model.get_evolution_prix(debut, fin)
    
    return format_response(evolution)
```

##### Liste complète des endpoints par controller :

**`prix_controller.py`** (`/api/prix/`)
- `GET /m2/<arrondissement>` - Prix/m² médian
- `GET /vente/<arrondissement>` - Valeur médiane des ventes
- `GET /evolution` - Évolution temporelle
- `GET /tendance/<arrondissement>` - Tendance et volatilité
- `GET /comparaison` - Comparaison entre arrondissements

**`logement_controller.py`** (`/api/logements/`)
- `GET /sociaux/<arrondissement>` - Logements sociaux APUR
- `GET /typologie/<arrondissement>` - Typologie appartements/maisons
- `GET /pieces/<arrondissement>` - Répartition T1/T2/T3/T4/T5+
- `GET /types/<arrondissement>` - Types de locaux par année

**`transport_controller.py`** (`/api/transport/`)
- `GET /metro/<arrondissement>` - Stations et lignes métro
- `GET /rer/<arrondissement>` - Lignes RER
- `GET /trafic/<arrondissement>` - Trafic total

**`pollution_controller.py`** (`/api/pollution/`)
- `GET /qualite/<arrondissement>` - Qualité de l'air
- `GET /polluants/<arrondissement>` - NO2, PM10, O3

---

#### 3. **SERVICES** (`backend/services/`)

**Responsabilité** : Logique réutilisable et chargement des données

##### `data_loader.py`
```python
import pandas as pd
from typing import Optional

class DataLoader:
    """Service de chargement des données Gold"""
    
    _data_cache = None
    
    @classmethod
    def load_data(cls) -> pd.DataFrame:
        """Charge le CSV Gold avec cache"""
        if cls._data_cache is None:
            cls._data_cache = pd.read_csv(
                'data/gold/dashboard_arrondissements_paris7.csv',
                sep=';'
            )
        return cls._data_cache
    
    @classmethod
    def get_arrondissement(cls, numero: int) -> Optional[dict]:
        """Retourne les données d'un arrondissement"""
        df = cls.load_data()
        row = df[df['Arrondissement'] == numero]
        if row.empty:
            return None
        return row.iloc[0].to_dict()
    
    @classmethod
    def get_all_arrondissements(cls) -> list:
        """Retourne tous les arrondissements"""
        df = cls.load_data()
        return df.to_dict('records')
```

---

#### 4. **VIEWS** (`backend/views/`)

**Responsabilité** : Formatage des réponses API

##### `response_formatter.py`
```python
from flask import jsonify
from typing import Any, Optional

def format_response(data: Any, status: int = 200, message: Optional[str] = None) -> tuple:
    """
    Formate une réponse API standardisée
    
    Returns:
        {
            "success": true,
            "data": {...},
            "message": "...",
            "timestamp": "2024-11-20T10:30:00"
        }
    """
    from datetime import datetime
    
    response = {
        'success': status < 400,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    return jsonify(response), status

def format_error(error: str, status: int = 400) -> tuple:
    """Formate une réponse d'erreur"""
    return format_response(
        data=None,
        status=status,
        message=error
    )
```

---

### Point d'entrée de l'API (`app.py`)

```python
from flask import Flask
from flask_cors import CORS
from controllers.prix_controller import prix_bp
from controllers.logement_controller import logement_bp
from controllers.transport_controller import transport_bp
from controllers.pollution_controller import pollution_bp
from middleware.error_handler import register_error_handlers

app = Flask(__name__)
CORS(app)

# Enregistrement des blueprints (controllers)
app.register_blueprint(prix_bp)
app.register_blueprint(logement_bp)
app.register_blueprint(transport_bp)
app.register_blueprint(pollution_bp)

# Middleware
register_error_handlers(app)

@app.route('/api/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 🎨 Architecture Frontend

### Structure des fichiers JS

#### `api.js` - Couche d'abstraction API
```javascript
class DashboardAPI {
  constructor(baseURL = 'http://localhost:5000/api') {
    this.baseURL = baseURL;
  }

  async getPrixM2(arrondissement, annee = 2024) {
    const response = await fetch(
      `${this.baseURL}/prix/m2/${arrondissement}?annee=${annee}`
    );
    return response.json();
  }

  async getLogementsSociaux(arrondissement) {
    const response = await fetch(
      `${this.baseURL}/logements/sociaux/${arrondissement}`
    );
    return response.json();
  }

  // Autres méthodes...
}
```

#### `map.js` - Gestion de la carte
```javascript
class ParisMap {
  constructor(containerId, api) {
    this.api = api;
    this.map = new maplibregl.Map({
      container: containerId,
      center: [2.3522, 48.8566],
      zoom: 11.5
    });
  }

  async loadArrondissements() {
    // Charge le GeoJSON
    // Colore selon les données
  }

  updateColors(metric) {
    // Met à jour la coloration
  }
}
```

---

## 🔄 Flux de données

```
┌─────────────────────────────────────────────────────────────┐
│                     SOURCES EXTERNES                         │
│  (DVF, Trafic Métro, Qualité Air, Stats INSEE)             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  BRONZE Layer │  (Données brutes)
         └───────┬───────┘
                 │ Scripts Python
                 │ (Nettoyage)
                 ▼
         ┌───────────────┐
         │  SILVER Layer │  (Données nettoyées)
         └───────┬───────┘
                 │ Scripts Python
                 │ (Agrégation)
                 ▼
         ┌───────────────┐
         │   GOLD Layer  │  (dashboard_arrondissements_paris7.csv)
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────────────────────────┐
         │       BACKEND API (MVC)            │
         │                                    │
         │  ┌────────────┐                   │
         │  │ Controllers│──┐                │
         │  └────────────┘  │                │
         │         │         │                │
         │         ▼         ▼                │
         │  ┌────────┐  ┌─────────┐          │
         │  │ Models │  │ Services│          │
         │  └────────┘  └─────────┘          │
         │         │         │                │
         │         └────┬────┘                │
         │              ▼                     │
         │       ┌───────────┐               │
         │       │   Views   │               │
         │       └─────┬─────┘               │
         └─────────────┼─────────────────────┘
                       │ JSON API
                       ▼
              ┌─────────────────┐
              │    FRONTEND     │
              │  (MapLibre JS)  │
              └─────────────────┘
```

---

## 📝 Résumé des avantages de cette architecture

| Aspect | Avantage |
|--------|----------|
| **Séparation claire** | Chaque couche a une responsabilité unique |
| **Testabilité** | Models et Services testables indépendamment |
| **Scalabilité** | Ajout facile de nouveaux endpoints |
| **Maintenabilité** | Code organisé et documenté |
| **Réutilisabilité** | Services et Models partagés entre controllers |
| **Data Pipeline** | Bronze→Silver→Gold permet traçabilité |
| **API REST** | Chaque métrique = endpoint dédié |
| **Frontend découplé** | Peut être remplacé sans toucher au backend |

---

## 🚀 Prochaines étapes

1. Créer la structure de dossiers
2. Implémenter les Models
3. Développer les Controllers et endpoints
4. Créer les Services de chargement de données
5. Implémenter le Frontend avec MapLibre
6. Tests unitaires et intégration
7. Documentation API (Swagger/OpenAPI)

