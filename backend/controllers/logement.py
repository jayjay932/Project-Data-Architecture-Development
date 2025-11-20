"""
Controller pour les endpoints liés aux logements (sociaux, typologie)
"""
from flask import Blueprint, request
import logging

logger = logging.getLogger(__name__)

# Création du Blueprint
logement_bp = Blueprint('logement', __name__, url_prefix='/api/logements')


@logement_bp.route('/sociaux/<int:arrondissement>', methods=['GET'])
def get_logements_sociaux(arrondissement: int):
    """
    GET /api/logements/sociaux/<arrondissement>
    
    Retourne les données sur les logements sociaux (APUR + estimation)
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "apur": {
                    "nb_logements_sociaux": null,
                    "part_pct": null
                },
                "estimation": "Faible (<10%)"
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
        
        return format_response({
            'arrondissement': arrondissement,
            'apur': arr.get_logements_sociaux_apur(),
            'estimation': arr.get_estimation_logement_social()
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_logements_sociaux: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@logement_bp.route('/typologie/<int:arrondissement>', methods=['GET'])
def get_typologie(arrondissement: int):
    """
    GET /api/logements/typologie/<arrondissement>?annee=2024
    
    Retourne la répartition par type de logement (appartement/maison)
    
    Query params:
        - annee (int): Année (2020-2025), défaut 2024
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "annee": 2024,
                "repartition": {
                    "appartement": {"nombre": 409, "pourcentage": 100.0},
                    "maison": {"nombre": 0, "pourcentage": 0.0},
                    "type_dominant": "Appartement"
                }
            }
        }
    """
    try:
        annee = request.args.get('annee', 2024, type=int)
        
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        if not 2020 <= annee <= 2025:
            return format_error(f"Année invalide : {annee}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        repartition = arr.get_repartition_types(annee)
        
        return format_response({
            'arrondissement': arrondissement,
            'annee': annee,
            'repartition': repartition
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_typologie: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@logement_bp.route('/pieces/<int:arrondissement>', methods=['GET'])
def get_repartition_pieces(arrondissement: int):
    """
    GET /api/logements/pieces/<arrondissement>?annee=2024
    
    Retourne la répartition par nombre de pièces (T1/T2/T3/T4/T5+)
    
    Query params:
        - annee (int): Année (2020-2025), défaut 2024
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "annee": 2024,
                "repartition": {
                    "T1": {"nombre": 105, "pourcentage": 25.7},
                    "T2": {"nombre": 120, "pourcentage": 29.3},
                    "T3": {"nombre": 93, "pourcentage": 22.7},
                    "T4": {"nombre": 31, "pourcentage": 7.6},
                    "T5plus": {"nombre": 59, "pourcentage": 14.4}
                }
            }
        }
    """
    try:
        annee = request.args.get('annee', 2024, type=int)
        
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        if not 2020 <= annee <= 2025:
            return format_error(f"Année invalide : {annee}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        repartition = arr.get_repartition_pieces(annee)
        
        return format_response({
            'arrondissement': arrondissement,
            'annee': annee,
            'repartition': repartition
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_repartition_pieces: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@logement_bp.route('/synthese/<int:arrondissement>', methods=['GET'])
def get_synthese_typologie(arrondissement: int):
    """
    GET /api/logements/synthese/<arrondissement>
    
    Retourne une synthèse de la typologie des logements (données 2024)
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "nb_appartements": 409,
                "nb_maisons": 0,
                "pct_appartements": 100.0,
                "nb_pieces_moyen": 2.6
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
        synthese = arr.get_synthese_typologie_2024()
        
        return format_response({
            'arrondissement': arrondissement,
            **synthese
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_synthese_typologie: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@logement_bp.route('/tous', methods=['GET'])
def get_tous_logements():
    """
    GET /api/logements/tous?annee=2024
    
    Retourne les données de logements pour tous les arrondissements
    
    Query params:
        - annee (int): Année pour les statistiques, défaut 2024
    
    Returns:
        {
            "success": true,
            "data": {
                "annee": 2024,
                "arrondissements": [
                    {
                        "arrondissement": 1,
                        "nb_appartements": 409,
                        "nb_maisons": 0,
                        ...
                    },
                    ...
                ]
            }
        }
    """
    try:
        annee = request.args.get('annee', 2024, type=int)
        
        # Validation
        if not 2020 <= annee <= 2025:
            return format_error(f"Année invalide : {annee}", status=400)
        
        # Chargement de tous les arrondissements
        tous_arrs = DataLoader.get_all_arrondissements()
        
        resultats = []
        for arr_data in tous_arrs:
            arr_num = int(arr_data['Arrondissement'])
            arr = Arrondissement(arr_num, arr_data)
            
            synthese = arr.get_synthese_typologie_2024()
            logements_sociaux = arr.get_logements_sociaux_apur()
            
            resultats.append({
                'arrondissement': arr_num,
                **synthese,
                'logements_sociaux_apur': logements_sociaux['nb_logements_sociaux'],
                'estimation_social': arr.get_estimation_logement_social()
            })
        
        return format_response({
            'annee': annee,
            'arrondissements': resultats
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_tous_logements: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


# Export du blueprint
__all__ = ['logement_bp']
