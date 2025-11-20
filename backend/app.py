"""
Application Flask principale - API Dashboard Immobilier Paris
"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging
from pathlib import Path
import sys
import os

# Ajouter le dossier racine au PYTHONPATH
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Imports des modules du projet
from config import get_config
from services.data_loader import DataLoader, initialize_data_loader
from controllers.prix import prix_bp
from controllers.logement import logement_bp
from controllers.transport import transport_bp
from controllers.pollution import pollution_bp
from middleware.error_handler  import register_error_handlers
from views.response_formatter import format_response, format_error


def create_app(config_name='development'):
    """
    Factory pour créer l'application Flask
    
    Args:
        config_name: Nom de la configuration ('development', 'production', 'testing')
    
    Returns:
        Application Flask configurée
    """
    app = Flask(__name__)
    
    # Chargement de la configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Configuration du logging
    logging.basicConfig(
        level=app.config.get('LOG_LEVEL', 'INFO'),
        format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Démarrage de l'application en mode {config_name}")
    
    # CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Initialisation du DataLoader
    try:
        data_path = config.GOLD_DATA_PATH
        initialize_data_loader(data_path)
        logger.info(f"DataLoader initialisé avec {data_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du DataLoader: {e}")
        logger.warning("L'application démarre sans données - vérifiez le fichier CSV Gold")
    
    # Enregistrement des Blueprints (Controllers)
    app.register_blueprint(prix_bp)
    app.register_blueprint(logement_bp)
    app.register_blueprint(transport_bp)
    app.register_blueprint(pollution_bp)
    logger.info("Blueprints enregistrés")
    
    # Middleware et error handlers
    register_error_handlers(app)
    
    # Routes de base
    @app.route('/')
    def index():
        """Page d'accueil de l'API"""
        return jsonify({
            'message': 'API Dashboard Immobilier Paris',
            'version': app.config.get('API_VERSION', 'v1'),
            'documentation': '/api/docs',
            'endpoints': {
                'health': '/api/health',
                'stats': '/api/stats',
                'arrondissements': '/api/arrondissements',
                'prix': '/api/prix/*',
                'logements': '/api/logements/*',
                'transport': '/api/transport/*',
                'pollution': '/api/pollution/*'
            }
        })
    
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        try:
            stats = DataLoader.get_stats_summary()
            return format_response({
                'status': 'healthy',
                'data_loaded': True,
                'nb_arrondissements': stats.get('nb_arrondissements', 0)
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return format_error(
                'Service unhealthy - vérifiez que le fichier CSV Gold existe',
                status=503
            )
    
    @app.route('/api/stats')
    def stats():
        """Statistiques globales de l'API"""
        try:
            stats = DataLoader.get_stats_summary()
            return format_response(stats)
        except Exception as e:
            logger.error(f"Erreur dans /api/stats: {e}")
            return format_error(f"Erreur: {str(e)}", status=500)
    
    @app.route('/api/arrondissements')
    def get_all_arrondissements():
        """Liste de tous les arrondissements"""
        try:
            tous_arrs = DataLoader.get_all_arrondissements()
            
            apercu = []
            for arr_data in tous_arrs:
                apercu.append({
                    'arrondissement': int(arr_data.get('Arrondissement', 0)),
                    'prix_m2_2024': arr_data.get('prix_m2_median_2024'),
                    'nb_ventes_2024': arr_data.get('nb_ventes_2024'),
                    'nb_stations_metro': arr_data.get('nb_stations_metro'),
                    'qualite_air': arr_data.get('qualite_air_dominante')
                })
            
            return format_response({
                'total': len(apercu),
                'arrondissements': apercu
            })
        except Exception as e:
            logger.error(f"Erreur dans /api/arrondissements: {e}")
            return format_error(f"Erreur: {str(e)}", status=500)
    
    @app.route('/api/arrondissements/<int:numero>')
    def get_arrondissement_complet(numero: int):
        """Données complètes d'un arrondissement"""
        try:
            if not 1 <= numero <= 20:
                return format_error(
                    f"Numéro d'arrondissement invalide: {numero}",
                    status=400
                )
            
            arr_data = DataLoader.get_arrondissement(numero)
            if not arr_data:
                return format_error(
                    f"Arrondissement {numero} non trouvé",
                    status=404
                )
            
            return format_response(arr_data)
        except Exception as e:
            logger.error(f"Erreur dans /api/arrondissements/{numero}: {e}")
            return format_error(f"Erreur: {str(e)}", status=500)
    
    logger.info("Application Flask créée avec succès")
    return app


# Point d'entrée pour le développement
if __name__ == '__main__':
    import os
    
    # Déterminer l'environnement
    env = os.getenv('FLASK_ENV', 'development')
    
    # Créer l'application
    app = create_app(env)
    
    # Lancer le serveur
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 70)
    print("🚀 DASHBOARD IMMOBILIER PARIS - API Backend")
    print("=" * 70)
    print(f"📡 API démarrée sur : http://localhost:{port}")
    print(f"🔍 Health check : http://localhost:{port}/api/health")
    print(f"📊 Stats : http://localhost:{port}/api/stats")
    print(f"🗺️  Arrondissements : http://localhost:{port}/api/arrondissements")
    print("=" * 70)
    print("Appuyez sur Ctrl+C pour arrêter le serveur")
    print()
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(env == 'development')
    )