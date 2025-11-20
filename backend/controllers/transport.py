"""
Controller pour les endpoints liés aux transports (métro, RER)
"""
from flask import Blueprint
import logging

logger = logging.getLogger(__name__)

# Création du Blueprint
transport_bp = Blueprint('transport', __name__, url_prefix='/api/transport')


@transport_bp.route('/<int:arrondissement>', methods=['GET'])
def get_transport(arrondissement: int):
    """
    GET /api/transport/<arrondissement>
    
    Retourne toutes les données de transport pour un arrondissement
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "metro": {
                    "nb_stations": 7,
                    "trafic_total": 33194770,
                    "nb_lignes": 6,
                    "lignes": ["1", "4", "7", "14", "11.0", "14.0"]
                },
                "rer": {
                    "nb_lignes": 2,
                    "lignes": ["A", "B"]
                }
            }
        }
    """
    try:
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        transport = arr.get_transport()
        
        return format_response({
            'arrondissement': arrondissement,
            **transport
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_transport: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@transport_bp.route('/metro/<int:arrondissement>', methods=['GET'])
def get_metro(arrondissement: int):
    """
    GET /api/transport/metro/<arrondissement>
    
    Retourne uniquement les données métro
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "nb_stations": 7,
                "trafic_total": 33194770,
                "nb_lignes": 6,
                "lignes": ["1", "4", "7", "14", "11.0", "14.0"]
            }
        }
    """
    try:
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        transport = arr.get_transport()
        
        return format_response({
            'arrondissement': arrondissement,
            **transport['metro']
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_metro: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@transport_bp.route('/rer/<int:arrondissement>', methods=['GET'])
def get_rer(arrondissement: int):
    """
    GET /api/transport/rer/<arrondissement>
    
    Retourne uniquement les données RER
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "nb_lignes": 2,
                "lignes": ["A", "B"]
            }
        }
    """
    try:
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        transport = arr.get_transport()
        
        return format_response({
            'arrondissement': arrondissement,
            **transport['rer']
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_rer: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@transport_bp.route('/classement', methods=['GET'])
def get_classement_transport():
    """
    GET /api/transport/classement?critere=nb_lignes_metro
    
    Classe les arrondissements selon un critère de transport
    
    Query params:
        - critere (str): 'nb_lignes_metro', 'trafic_total', 'nb_stations', défaut 'nb_lignes_metro'
    
    Returns:
        {
            "success": true,
            "data": {
                "critere": "nb_lignes_metro",
                "classement": [
                    {"arrondissement": 8, "valeur": 12},
                    {"arrondissement": 12, "valeur": 9},
                    ...
                ]
            }
        }
    """
    try:
        critere = request.args.get('critere', 'nb_lignes_metro', type=str)
        
        # Validation du critère
        criteres_valides = ['nb_lignes_metro', 'trafic_total_metro', 'nb_stations_metro', 'nb_lignes_rer']
        if critere not in criteres_valides:
            return format_error(
                f"Critère invalide : {critere}. Doit être parmi {criteres_valides}",
                status=400
            )
        
        # Chargement de tous les arrondissements
        tous_arrs = DataLoader.get_all_arrondissements()
        
        classement = []
        for arr_data in tous_arrs:
            arr_num = int(arr_data['Arrondissement'])
            valeur = arr_data.get(critere)
            
            if valeur is not None:
                classement.append({
                    'arrondissement': arr_num,
                    'valeur': float(valeur) if isinstance(valeur, (int, float)) else valeur
                })
        
        # Tri décroissant
        classement.sort(key=lambda x: x['valeur'] if x['valeur'] is not None else 0, reverse=True)
        
        return format_response({
            'critere': critere,
            'classement': classement
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_classement_transport: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


# Export du blueprint
__all__ = ['transport_bp']
