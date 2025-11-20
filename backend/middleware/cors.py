"""
Middleware pour la gestion des CORS
"""
from flask import Flask
from flask_cors import CORS
import logging

logger = logging.getLogger(__name__)


def setup_cors(app: Flask, origins: list = None):
    """
    Configure CORS pour l'application Flask
    
    Args:
        app: Instance Flask
        origins: Liste des origines autorisées (None = toutes)
    """
    if origins is None or '*' in origins:
        # Développement : autoriser toutes les origines
        CORS(app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": False,
                "max_age": 3600
            }
        })
        logger.info("CORS configuré : toutes origines autorisées (dev)")
    else:
        # Production : origines spécifiques
        CORS(app, resources={
            r"/api/*": {
                "origins": origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": True,
                "max_age": 3600
            }
        })
        logger.info(f"CORS configuré : origines = {origins}")


def add_cors_headers(response):
    """
    Ajoute manuellement les headers CORS à une réponse
    
    Args:
        response: Objet Response Flask
        
    Returns:
        Response avec headers CORS
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
