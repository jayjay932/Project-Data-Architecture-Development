"""
Controller pour les endpoints liés à la qualité de l'air et pollution
"""
from flask import Blueprint, request
import logging

logger = logging.getLogger(__name__)

# Création du Blueprint
pollution_bp = Blueprint('pollution', __name__, url_prefix='/api/pollution')


@pollution_bp.route('/<int:arrondissement>', methods=['GET'])
def get_qualite_air(arrondissement: int):
    """
    GET /api/pollution/<arrondissement>
    
    Retourne toutes les données de qualité de l'air
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "no2_moyen": 34.6,
                "pm10_moyen": 31.4,
                "o3_moyen": 37.0,
                "qualite_dominante": "Moyenne"
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
        qualite = arr.get_qualite_air()
        
        return format_response({
            'arrondissement': arrondissement,
            **qualite
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_qualite_air: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@pollution_bp.route('/polluant/<string:polluant>', methods=['GET'])
def get_classement_polluant(polluant: str):
    """
    GET /api/pollution/polluant/<polluant>?ordre=asc
    
    Classe les arrondissements selon un polluant
    
    Path params:
        - polluant: 'no2', 'pm10', ou 'o3'
    
    Query params:
        - ordre (str): 'asc' (croissant) ou 'desc' (décroissant), défaut 'desc'
    
    Returns:
        {
            "success": true,
            "data": {
                "polluant": "no2",
                "unite": "µg/m³",
                "classement": [
                    {"arrondissement": 17, "valeur": 37.2},
                    {"arrondissement": 8, "valeur": 36.0},
                    ...
                ]
            }
        }
    """
    try:
        ordre = request.args.get('ordre', 'desc', type=str)
        
        # Validation
        polluants_valides = ['no2', 'pm10', 'o3']
        if polluant not in polluants_valides:
            return format_error(
                f"Polluant invalide : {polluant}. Doit être parmi {polluants_valides}",
                status=400
            )
        
        if ordre not in ['asc', 'desc']:
            return format_error("L'ordre doit être 'asc' ou 'desc'", status=400)
        
        # Chargement de tous les arrondissements
        tous_arrs = DataLoader.get_all_arrondissements()
        
        classement = []
        colonne = f'{polluant}_moyen'
        
        for arr_data in tous_arrs:
            arr_num = int(arr_data['Arrondissement'])
            valeur = arr_data.get(colonne)
            
            if valeur is not None:
                classement.append({
                    'arrondissement': arr_num,
                    'valeur': float(valeur)
                })
        
        # Tri selon l'ordre demandé
        reverse = (ordre == 'desc')
        classement.sort(key=lambda x: x['valeur'], reverse=reverse)
        
        return format_response({
            'polluant': polluant,
            'unite': 'µg/m³',
            'ordre': ordre,
            'classement': classement
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_classement_polluant: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@pollution_bp.route('/statistiques', methods=['GET'])
def get_statistiques_pollution():
    """
    GET /api/pollution/statistiques
    
    Retourne des statistiques globales sur la pollution à Paris
    
    Returns:
        {
            "success": true,
            "data": {
                "no2": {
                    "moyenne": 35.5,
                    "min": 33.1,
                    "max": 37.4,
                    "arrondissement_min": 15,
                    "arrondissement_max": 19
                },
                "pm10": {...},
                "o3": {...}
            }
        }
    """
    try:
        # Chargement de tous les arrondissements
        tous_arrs = DataLoader.get_all_arrondissements()
        
        statistiques = {}
        
        for polluant in ['no2', 'pm10', 'o3']:
            colonne = f'{polluant}_moyen'
            valeurs = []
            
            for arr_data in tous_arrs:
                valeur = arr_data.get(colonne)
                if valeur is not None:
                    valeurs.append({
                        'arr': int(arr_data['Arrondissement']),
                        'val': float(valeur)
                    })
            
            if valeurs:
                valeurs_sorted = sorted(valeurs, key=lambda x: x['val'])
                
                statistiques[polluant] = {
                    'moyenne': round(sum(v['val'] for v in valeurs) / len(valeurs), 1),
                    'min': valeurs_sorted[0]['val'],
                    'max': valeurs_sorted[-1]['val'],
                    'arrondissement_min': valeurs_sorted[0]['arr'],
                    'arrondissement_max': valeurs_sorted[-1]['arr']
                }
        
        return format_response(statistiques)
    
    except Exception as e:
        logger.error(f"Erreur dans get_statistiques_pollution: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@pollution_bp.route('/qualite/repartition', methods=['GET'])
def get_repartition_qualite():
    """
    GET /api/pollution/qualite/repartition
    
    Retourne la répartition des arrondissements par qualité de l'air
    
    Returns:
        {
            "success": true,
            "data": {
                "repartition": {
                    "Bonne": 0,
                    "Moyenne": 20,
                    "Médiocre": 0,
                    "Mauvaise": 0
                },
                "details": [
                    {"qualite": "Moyenne", "arrondissements": [1,2,3,...]},
                    ...
                ]
            }
        }
    """
    try:
        # Chargement de tous les arrondissements
        tous_arrs = DataLoader.get_all_arrondissements()
        
        repartition = {}
        details = {}
        
        for arr_data in tous_arrs:
            arr_num = int(arr_data['Arrondissement'])
            qualite = arr_data.get('qualite_air_dominante')
            
            if qualite:
                repartition[qualite] = repartition.get(qualite, 0) + 1
                
                if qualite not in details:
                    details[qualite] = []
                details[qualite].append(arr_num)
        
        # Formater les détails
        details_list = [
            {'qualite': q, 'arrondissements': sorted(arrs)}
            for q, arrs in details.items()
        ]
        
        return format_response({
            'repartition': repartition,
            'details': details_list
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_repartition_qualite: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


# Export du blueprint
__all__ = ['pollution_bp']
