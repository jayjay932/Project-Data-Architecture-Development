"""
Formatage standardisé des réponses API
"""
from flask import jsonify
from typing import Any, Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def format_response(
    data: Any,
    status: int = 200,
    message: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> tuple:
    """
    Formate une réponse API standardisée
    
    Args:
        data: Données à retourner
        status: Code HTTP de statut
        message: Message optionnel
        metadata: Métadonnées supplémentaires (pagination, etc.)
        
    Returns:
        Tuple (response_dict, status_code) pour Flask
        
    Format de réponse:
        {
            "success": true,
            "data": {...},
            "message": "...",
            "metadata": {...},
            "timestamp": "2024-11-20T10:30:00.000Z"
        }
    """
    response = {
        'success': status < 400,
        'data': data,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if message:
        response['message'] = message
    
    if metadata:
        response['metadata'] = metadata
    
    return jsonify(response), status


def format_error(
    error: str,
    status: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None
) -> tuple:
    """
    Formate une réponse d'erreur
    
    Args:
        error: Message d'erreur
        status: Code HTTP de statut
        error_code: Code d'erreur applicatif
        details: Détails supplémentaires sur l'erreur
        
    Returns:
        Tuple (response_dict, status_code) pour Flask
        
    Format d'erreur:
        {
            "success": false,
            "error": {
                "message": "...",
                "code": "...",
                "details": {...}
            },
            "timestamp": "2024-11-20T10:30:00.000Z"
        }
    """
    logger.warning(f"Erreur API : {error} (status={status})")
    
    error_obj = {
        'message': error
    }
    
    if error_code:
        error_obj['code'] = error_code
    
    if details:
        error_obj['details'] = details
    
    response = {
        'success': False,
        'error': error_obj,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    return jsonify(response), status


def format_validation_error(errors: Dict[str, List[str]]) -> tuple:
    """
    Formate une erreur de validation
    
    Args:
        errors: Dictionnaire des erreurs de validation
        
    Returns:
        Réponse formatée avec status 422
    """
    return format_error(
        error="Erreur de validation des données",
        status=422,
        error_code="VALIDATION_ERROR",
        details={'fields': errors}
    )


def format_not_found(resource: str, identifier: Any) -> tuple:
    """
    Formate une erreur 404 (ressource non trouvée)
    
    Args:
        resource: Type de ressource
        identifier: Identifiant de la ressource
        
    Returns:
        Réponse formatée avec status 404
    """
    return format_error(
        error=f"{resource} non trouvé(e)",
        status=404,
        error_code="NOT_FOUND",
        details={
            'resource': resource,
            'identifier': identifier
        }
    )


def format_paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total: int
) -> tuple:
    """
    Formate une réponse paginée
    
    Args:
        data: Données de la page courante
        page: Numéro de page (commence à 1)
        page_size: Taille de la page
        total: Nombre total d'éléments
        
    Returns:
        Réponse formatée avec métadonnées de pagination
    """
    total_pages = (total + page_size - 1) // page_size  # Division arrondie vers le haut
    
    metadata = {
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return format_response(
        data=data,
        metadata=metadata
    )


def format_list_response(
    items: List[Any],
    resource_name: str,
    filters: Optional[Dict] = None
) -> tuple:
    """
    Formate une réponse pour une liste de ressources
    
    Args:
        items: Liste des éléments
        resource_name: Nom de la ressource (au pluriel)
        filters: Filtres appliqués
        
    Returns:
        Réponse formatée avec métadonnées
    """
    metadata = {
        'count': len(items),
        'resource': resource_name
    }
    
    if filters:
        metadata['filters'] = filters
    
    return format_response(
        data=items,
        metadata=metadata
    )


def format_single_resource(
    item: Dict[str, Any],
    resource_name: str
) -> tuple:
    """
    Formate une réponse pour une ressource unique
    
    Args:
        item: Données de la ressource
        resource_name: Nom de la ressource
        
    Returns:
        Réponse formatée
    """
    return format_response(
        data=item,
        metadata={'resource': resource_name}
    )


# Helpers pour les erreurs HTTP courantes

def bad_request(message: str = "Requête invalide") -> tuple:
    """Erreur 400 - Bad Request"""
    return format_error(message, status=400, error_code="BAD_REQUEST")


def unauthorized(message: str = "Non autorisé") -> tuple:
    """Erreur 401 - Unauthorized"""
    return format_error(message, status=401, error_code="UNAUTHORIZED")


def forbidden(message: str = "Accès interdit") -> tuple:
    """Erreur 403 - Forbidden"""
    return format_error(message, status=403, error_code="FORBIDDEN")


def not_found(message: str = "Ressource non trouvée") -> tuple:
    """Erreur 404 - Not Found"""
    return format_error(message, status=404, error_code="NOT_FOUND")


def internal_error(message: str = "Erreur interne du serveur") -> tuple:
    """Erreur 500 - Internal Server Error"""
    return format_error(message, status=500, error_code="INTERNAL_ERROR")
