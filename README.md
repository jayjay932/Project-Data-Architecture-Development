# 🏠 Dashboard Immobilier Paris

Dashboard interactif d'analyse immobilière par arrondissement de Paris, avec architecture MVC complète.

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [API Documentation](#api-documentation)
- [Structure du projet](#structure-du-projet)
- [Technologies](#technologies)
- [Développement](#développement)
- [Déploiement](#déploiement)

---

## 🎯 Vue d'ensemble

Ce projet propose un **dashboard interactif** permettant d'explorer les données immobilières des 20 arrondissements de Paris à travers :

- 📊 **Prix et marché** : Prix/m², évolutions temporelles (2020-2025)
- 🏢 **Logements** : Typologie, logements sociaux, répartition par pièces
- 🚇 **Transport** : Stations et lignes de métro/RER, trafic
- 🌫️ **Qualité de l'air** : NO2, PM10, O3

### Fonctionnalités principales

✅ Carte interactive avec coloration dynamique  
✅ API REST complète avec architecture MVC  
✅ Visualisation multi-critères (prix, transport, pollution)  
✅ Panneau de détails par arrondissement  
✅ Export des données (JSON/CSV)  
✅ Responsive design

---

## 🏗️ Architecture

Le projet suit une **architecture MVC (Model-View-Controller)** avec un pipeline de données en 3 couches (Bronze/Silver/Gold) :

```
DATA PIPELINE (ETL)           BACKEND (MVC)              FRONTEND
================            ==================         ============
Bronze (Données brutes)    
    ↓                      
Silver (Nettoyées)         → Models                  
    ↓                         ↓                      
Gold (Agrégées)            → Controllers → Views   →  MapLibre + UI
                              ↓
                           Services
```

### Justification du MVC

1. **Séparation des responsabilités** : Models (données), Controllers (logique), Views (API)
2. **Maintenabilité** : Modifications isolées sans impact sur les autres couches
3. **Testabilité** : Chaque composant testable indépendamment
4. **Scalabilité** : Ajout facile de nouveaux endpoints et fonctionnalités

👉 Voir [ARCHITECTURE.md](docs/ARCHITECTURE.md) pour plus de détails

---

## 🚀 Installation

### Prérequis

- Python 3.8+
- pip
- Navigateur web moderne

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd projet_data_architecture
```

### 2. Installer les dépendances backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Vérifier les données

Assurez-vous que le fichier `data/gold/dashboard_arrondissements_paris7.csv` existe.

### 4. Configuration

Créer un fichier `.env` dans le dossier `backend/` :

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=votre-clé-secrète
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

---

## 💻 Utilisation

### Démarrer le backend

```bash
cd backend
python app.py
```

L'API sera disponible sur `http://localhost:5000`

### Ouvrir le frontend

```bash
# Option 1 : Serveur HTTP simple
cd frontend
python -m http.server 8000

# Option 2 : Live Server (VS Code extension)
# Clic droit sur index.html → Open with Live Server
```

Le dashboard sera disponible sur `http://localhost:8000`

### Vérifier l'API

```bash
curl http://localhost:5000/api/health
```

Réponse attendue :
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "data_loaded": true,
    "nb_arrondissements": 20
  }
}
```

---

## 📡 API Documentation

### Endpoints principaux

#### **Prix & Marché** (`/api/prix/*`)

```bash
# Prix/m² médian d'un arrondissement
GET /api/prix/m2/<arrondissement>?annee=2024

# Évolution des prix
GET /api/prix/evolution/<arrondissement>?debut=2020&fin=2024&type=prix_m2

# Tendance du marché
GET /api/prix/tendance/<arrondissement>

# Comparaison entre arrondissements
GET /api/prix/comparaison?arrondissements=1,2,3&annee=2024
```

#### **Logements** (`/api/logements/*`)

```bash
# Logements sociaux
GET /api/logements/sociaux/<arrondissement>

# Typologie (appartements/maisons)
GET /api/logements/typologie/<arrondissement>?annee=2024

# Répartition par nombre de pièces
GET /api/logements/pieces/<arrondissement>?annee=2024
```

#### **Transport** (`/api/transport/*`)

```bash
# Toutes les données de transport
GET /api/transport/<arrondissement>

# Métro uniquement
GET /api/transport/metro/<arrondissement>

# Classement par critère
GET /api/transport/classement?critere=nb_lignes_metro
```

#### **Pollution** (`/api/pollution/*`)

```bash
# Qualité de l'air
GET /api/pollution/<arrondissement>

# Classement par polluant
GET /api/pollution/polluant/<no2|pm10|o3>?ordre=desc

# Statistiques globales
GET /api/pollution/statistiques
```

#### **Général**

```bash
# Tous les arrondissements (synthèse)
GET /api/arrondissements

# Données complètes d'un arrondissement
GET /api/arrondissements/<numero>

# Statistiques générales
GET /api/stats
```

### Format des réponses

Toutes les réponses suivent le format :

```json
{
  "success": true,
  "data": {...},
  "timestamp": "2024-11-20T10:30:00.000Z"
}
```

En cas d'erreur :

```json
{
  "success": false,
  "error": {
    "message": "...",
    "code": "ERROR_CODE"
  },
  "timestamp": "2024-11-20T10:30:00.000Z"
}
```

---

## 📂 Structure du projet

```
projet_data_architecture/
├── data/
│   ├── bronze/          # Données brutes
│   ├── silver/          # Données nettoyées
│   ├── gold/            # Données agrégées
│   └── processing/      # Scripts de transformation
│
├── backend/             # API Backend (Flask)
│   ├── app.py           # Point d'entrée
│   ├── config.py        # Configuration
│   ├── models/          # Models (logique métier)
│   ├── controllers/     # Controllers (endpoints)
│   ├── services/        # Services (data loader, etc.)
│   ├── views/           # Views (formatage réponses)
│   ├── middleware/      # Middleware (erreurs, CORS)
│   └── tests/           # Tests unitaires
│
├── frontend/            # Frontend (HTML/CSS/JS)
│   ├── index.html       # Page principale
│   ├── assets/
│   │   ├── css/         # Styles
│   │   └── js/          # Scripts (API, Map, UI)
│   └── components/      # Composants réutilisables
│
├── docs/                # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
│
└── README.md            # Ce fichier
```

---

## 🛠️ Technologies

### Backend
- **Flask** 3.0 : Framework web Python
- **Pandas** : Manipulation de données
- **Flask-CORS** : Gestion des CORS

### Frontend
- **MapLibre GL** : Cartographie interactive
- **Vanilla JavaScript** : Pas de framework lourd
- **CSS3** : Design moderne et responsive

### Data Pipeline
- **Python** : Scripts ETL (Bronze → Silver → Gold)
- **Pandas/Numpy** : Traitement de données

---

## 👨‍💻 Développement

### Lancer les tests

```bash
cd backend
pytest
```

### Linter et formatage

```bash
# Black (formatage)
black backend/

# Flake8 (linting)
flake8 backend/

# MyPy (type checking)
mypy backend/
```

### Recharger les données

```bash
cd data/processing
python 02_silver_to_gold.py
```

### Ajouter un nouveau endpoint

1. Créer une méthode dans le Model correspondant
2. Ajouter une route dans le Controller
3. Optionnel : Ajouter la méthode dans le client API frontend

Exemple :

```python
# backend/controllers/prix_controller.py
@prix_bp.route('/nouveau/<int:arrondissement>')
def nouveau_endpoint(arrondissement):
    arr_data = DataLoader.get_arrondissement(arrondissement)
    arr = Arrondissement(arrondissement, arr_data)
    
    result = arr.ma_nouvelle_methode()
    return format_response(result)
```

---

## 🚀 Déploiement

### Backend (Heroku / Railway)

```bash
# Créer un Procfile
echo "web: gunicorn app:app" > Procfile

# Ajouter gunicorn
pip install gunicorn
pip freeze > requirements.txt

# Déployer
git push heroku main
```

### Frontend (Netlify / Vercel)

1. Configurer l'URL de l'API dans `frontend/assets/js/api.js`
2. Build et deploy via Git

### Docker (optionnel)

```dockerfile
# Backend
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["python", "app.py"]
```

---

## 📊 Métriques disponibles

### Prix & Marché
- Prix/m² médian (2020-2025)
- Prix médian des ventes
- Évolution temporelle
- Tendance et volatilité
- Volume de ventes

### Logements
- Nombre d'appartements/maisons
- Répartition T1/T2/T3/T4/T5+
- Logements sociaux (APUR)
- Nombre de pièces moyen

### Transport
- Stations de métro
- Lignes de métro et RER
- Trafic total

### Pollution
- NO2, PM10, O3 moyens
- Qualité de l'air dominante

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements
4. Push et créer une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 📧 Contact

Pour toute question : [votre-email]

---

## 🙏 Crédits

- Données DVF : [data.gouv.fr](https://data.gouv.fr)
- Données transport : [RATP Open Data](https://data.ratp.fr)
- Carte : [MapLibre GL](https://maplibre.org)
- GeoJSON Paris : [Paris Open Data](https://opendata.paris.fr)
