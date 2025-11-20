"""
Middleware pour le logging des requêtes
"""
from flask import Flask, request, g
import logging
import time
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)


def setup_logging(app: Flask, log_level: str = 'INFO'):
    """
    Configure le système de logging
    
    Args:
        app: Instance Flask
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
    """
    # Configuration du format
    log_handler = logging.StreamHandler()
    
    # Format JSON pour faciliter le parsing (production)
    if app.config.get('ENV') == 'production':
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        # Format simple pour le développement
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    log_handler.setFormatter(formatter)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(log_handler)
    
    logger.info(f"Logging configuré : niveau = {log_level}")


def log_request_middleware(app: Flask):
    """
    Enregistre toutes les requêtes HTTP
    
    Args:
        app: Instance Flask
    """
    
    @app.before_request
    def before_request():
        """Appelé avant chaque requête"""
        g.start_time = time.time()
        
        logger.info(
            f"Request started",
            extra={
                'method': request.method,
                'path': request.path,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
        )
    
    @app.after_request
    def after_request(response):
        """Appelé après chaque requête"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            logger.info(
                f"Request completed",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'ip': request.remote_addr
                }
            )
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Appelé en cas d'exception"""
        if exception:
            logger.error(
                f"Request failed",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'error': str(exception)
                },
                exc_info=True
            )
    
    logger.info("Request logging middleware activé")


class RequestIDMiddleware:
    """
    Middleware pour ajouter un ID unique à chaque requête
    """
    
    def __init__(self, app: Flask):
        """
        Initialise le middleware
        
        Args:
            app: Instance Flask
        """
        self.app = app
        app.before_request(self.before_request)
    
    def before_request(self):
        """Génère un ID unique pour la requête"""
        import uuid
        g.request_id = str(uuid.uuid4())
        
    @staticmethod
    def get_request_id() -> str:
        """
        Récupère l'ID de la requête courante
        
        Returns:
            ID de la requête
        """
        return getattr(g, 'request_id', 'unknown')
