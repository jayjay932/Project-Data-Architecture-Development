"""
Middleware pour la gestion des erreurs de l'API
"""
from flask import Flask
from werkzeug.exceptions import HTTPException
import logging

from views.response_formatter import format_error

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    """
    Enregistre les gestionnaires d'erreurs pour l'application Flask
    
    Args:
        app: Instance Flask
    """
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Gestion des erreurs 400 Bad Request"""
        logger.warning(f"Erreur 400: {error}")
        return format_error(
            str(error.description) if hasattr(error, 'description') else "Requête invalide",
            status=400,
            error_code='BAD_REQUEST'
        )
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Gestion des erreurs 404 Not Found"""
        logger.warning(f"Erreur 404: {error}")
        return format_error(
            "Ressource non trouvée",
            status=404,
            error_code='NOT_FOUND'
        )
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Gestion des erreurs 405 Method Not Allowed"""
        logger.warning(f"Erreur 405: {error}")
        return format_error(
            "Méthode HTTP non autorisée",
            status=405,
            error_code='METHOD_NOT_ALLOWED'
        )
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Gestion des erreurs 500 Internal Server Error"""
        logger.error(f"Erreur 500: {error}", exc_info=True)
        return format_error(
            "Erreur interne du serveur",
            status=500,
            error_code='INTERNAL_ERROR'
        )
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Gestionnaire générique pour toutes les exceptions HTTP"""
        logger.warning(f"Exception HTTP {error.code}: {error}")
        return format_error(
            error.description,
            status=error.code,
            error_code=f'HTTP_{error.code}'
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Gestionnaire pour les erreurs inattendues"""
        logger.error(f"Erreur inattendue: {error}", exc_info=True)
        return format_error(
            "Une erreur inattendue s'est produite",
            status=500,
            error_code='UNEXPECTED_ERROR'
        )
    
    logger.info("Gestionnaires d'erreurs enregistrés")
