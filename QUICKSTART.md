# 🚀 Guide de Démarrage Rapide

Ce guide vous permettra de démarrer le Dashboard Immobilier Paris en **moins de 5 minutes**.

## ⚡ Démarrage ultra-rapide

### 1. Installation (2 minutes)

```bash
# Cloner et entrer dans le projet
git clone <votre-repo>
cd projet_data_architecture

# Installer les dépendances backend
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Lancer le backend (30 secondes)

```bash
cd backend
python app.py
```

✅ L'API est maintenant disponible sur `http://localhost:5000`

### 3. Ouvrir le frontend (30 secondes)

```bash
# Dans un nouveau terminal
cd frontend
python -m http.server 8000
```

✅ Le dashboard est maintenant disponible sur `http://localhost:8000`

### 4. Profiter ! 🎉

Ouvrez votre navigateur sur `http://localhost:8000` et explorez les données !

---

## 🔍 Vérification rapide

### Tester l'API

```bash
# Test de santé
curl http://localhost:5000/api/health

# Récupérer les données du 1er arrondissement
curl http://localhost:5000/api/arrondissements/1
```

### Tester le frontend

1. Ouvrez `http://localhost:8000`
2. La carte de Paris devrait apparaître
3. Survolez un arrondissement pour voir les données
4. Cliquez pour voir les détails

---

## 📦 Fichiers essentiels

### Backend

- `backend/app.py` : Point d'entrée de l'API
- `backend/config.py` : Configuration
- `backend/controllers/` : Endpoints de l'API
- `backend/models/` : Logique métier

### Frontend

- `frontend/index.html` : Page principale
- `frontend/assets/js/api.js` : Client API
- `frontend/assets/js/map.js` : Gestion de la carte
- `frontend/assets/js/main.js` : Point d'entrée

### Données

- `data/gold/dashboard_arrondissements_paris7.csv` : Données agrégées (REQUIS)

---

## 🛠️ Configuration avancée (optionnel)

### Variables d'environnement

Créer `backend/.env` :

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=votre-clé-secrète-change-moi
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

### Changer le port du backend

```bash
# Dans backend/app.py, modifier la ligne :
app.run(host='0.0.0.0', port=5000, debug=True)

# Puis dans frontend/assets/js/api.js, modifier :
constructor(baseURL = 'http://localhost:VOTRE_PORT/api')
```

---

## 🐛 Résolution des problèmes courants

### Problème : "Module not found"

```bash
cd backend
pip install -r requirements.txt
```

### Problème : "API not accessible"

1. Vérifiez que le backend est démarré (`python app.py`)
2. Vérifiez l'URL dans `frontend/assets/js/api.js`
3. Testez : `curl http://localhost:5000/api/health`

### Problème : "Données non trouvées"

Vérifiez que le fichier existe :
```bash
ls data/gold/dashboard_arrondissements_paris7.csv
```

### Problème : "CORS error"

Ajoutez dans `backend/.env` :
```env
CORS_ORIGINS=*
```

---

## 📖 Prochaines étapes

### Explorer les données

- 📊 Changez la métrique affichée (prix, transport, pollution)
- 🗺️ Cliquez sur un arrondissement pour voir les détails
- 📈 Comparez les évolutions temporelles

### Personnaliser

- 🎨 Modifier les couleurs dans `frontend/assets/css/style.css`
- 🔧 Ajouter de nouveaux endpoints dans `backend/controllers/`
- 📊 Créer de nouvelles visualisations

### Déployer

Consultez la section **Déploiement** du README principal.

---

## 💡 Commandes utiles

```bash
# Backend
python app.py                    # Démarrer l'API
pytest                           # Lancer les tests
black .                          # Formater le code

# Frontend
python -m http.server 8000       # Serveur de développement
```

---

## 🆘 Besoin d'aide ?

- 📖 Consultez [README.md](README.md) pour la documentation complète
- 🏗️ Consultez [ARCHITECTURE.md](docs/ARCHITECTURE.md) pour l'architecture
- 📡 Consultez [API.md](docs/API.md) pour la documentation de l'API
- 🐛 Ouvrez une issue sur GitHub

---

## ✅ Checklist de démarrage

- [ ] Backend installé et démarré
- [ ] Frontend accessible
- [ ] API répond aux requêtes
- [ ] Carte affichée correctement
- [ ] Données chargées

**Tout fonctionne ?** Félicitations ! 🎉 Vous pouvez maintenant explorer le dashboard !

---

*Temps total estimé : **5 minutes***
