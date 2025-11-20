"""
Controller pour les endpoints liés aux prix et au marché immobilier
"""
from flask import Blueprint, request
from typing import Optional
import logging

# Imports locaux (à adapter selon votre structure)
# from models.arrondissement import Arrondissement
# from services.data_loader import DataLoader
# from views.response_formatter import format_response, format_error, format_not_found

logger = logging.getLogger(__name__)

# Création du Blueprint
prix_bp = Blueprint('prix', __name__, url_prefix='/api/prix')


@prix_bp.route('/m2/<int:arrondissement>', methods=['GET'])
def get_prix_m2(arrondissement: int):
    """
    GET /api/prix/m2/<arrondissement>?annee=2024
    
    Retourne le prix/m² médian pour un arrondissement et une année
    
    Query params:
        - annee (int, optionnel): Année (2020-2025), défaut 2024
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "annee": 2024,
                "prix_m2_median": 12586
            }
        }
    """
    try:
        # Récupération des paramètres
        annee = request.args.get('annee', 2024, type=int)
        
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(
                f"Arrondissement invalide : {arrondissement}. Doit être entre 1 et 20.",
                status=400
            )
        
        if not 2020 <= annee <= 2025:
            return format_error(
                f"Année invalide : {annee}. Doit être entre 2020 et 2025.",
                status=400
            )
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        # Création du model
        arr = Arrondissement(arrondissement, arr_data)
        prix_m2 = arr.get_prix_m2_median(annee)
        
        # Réponse
        return format_response({
            'arrondissement': arrondissement,
            'annee': annee,
            'prix_m2_median': prix_m2
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_prix_m2: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@prix_bp.route('/vente/<int:arrondissement>', methods=['GET'])
def get_prix_vente(arrondissement: int):
    """
    GET /api/prix/vente/<arrondissement>?annee=2024
    
    Retourne le prix médian des ventes pour un arrondissement
    
    Query params:
        - annee (int, optionnel): Année (2020-2025), défaut 2024
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "annee": 2024,
                "prix_median": 560000,
                "nb_ventes": 882
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
        
        return format_response({
            'arrondissement': arrondissement,
            'annee': annee,
            'prix_median': arr.get_prix_median(annee),
            'nb_ventes': arr.get_nb_ventes(annee)
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_prix_vente: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@prix_bp.route('/evolution/<int:arrondissement>', methods=['GET'])
def get_evolution_prix(arrondissement: int):
    """
    GET /api/prix/evolution/<arrondissement>?debut=2020&fin=2024&type=prix_m2
    
    Retourne l'évolution des prix entre deux années
    
    Query params:
        - debut (int): Année de début (2020-2024)
        - fin (int): Année de fin (2021-2025)
        - type (str): 'prix' ou 'prix_m2', défaut 'prix_m2'
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "periode": {
                    "debut": 2020,
                    "fin": 2024
                },
                "type": "prix_m2",
                "evolution_pct": -6.8,
                "valeur_debut": 13511,
                "valeur_fin": 12586
            }
        }
    """
    try:
        # Paramètres
        annee_debut = request.args.get('debut', 2020, type=int)
        annee_fin = request.args.get('fin', 2024, type=int)
        type_prix = request.args.get('type', 'prix_m2', type=str)
        
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        if not 2020 <= annee_debut <= 2024:
            return format_error(f"Année de début invalide : {annee_debut}", status=400)
        if not 2021 <= annee_fin <= 2025:
            return format_error(f"Année de fin invalide : {annee_fin}", status=400)
        if annee_debut >= annee_fin:
            return format_error("L'année de début doit être antérieure à l'année de fin", status=400)
        if type_prix not in ['prix', 'prix_m2']:
            return format_error(f"Type invalide : {type_prix}. Doit être 'prix' ou 'prix_m2'", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        
        # Récupération de l'évolution
        if type_prix == 'prix_m2':
            evolution_pct = arr.get_evolution_prix_m2(annee_debut, annee_fin)
            valeur_debut = arr.get_prix_m2_median(annee_debut)
            valeur_fin = arr.get_prix_m2_median(annee_fin)
        else:
            evolution_pct = arr.get_evolution_prix(annee_debut, annee_fin)
            valeur_debut = arr.get_prix_median(annee_debut)
            valeur_fin = arr.get_prix_median(annee_fin)
        
        return format_response({
            'arrondissement': arrondissement,
            'periode': {
                'debut': annee_debut,
                'fin': annee_fin
            },
            'type': type_prix,
            'evolution_pct': evolution_pct,
            'valeur_debut': valeur_debut,
            'valeur_fin': valeur_fin
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_evolution_prix: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@prix_bp.route('/tendance/<int:arrondissement>', methods=['GET'])
def get_tendance(arrondissement: int):
    """
    GET /api/prix/tendance/<arrondissement>
    
    Retourne la tendance du marché et la volatilité
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "tendance": "Stable",
                "evolution_annuelle_moyenne_pct": -1.5,
                "volatilite": 2.5
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
        tendance = arr.get_tendance_prix()
        
        return format_response({
            'arrondissement': arrondissement,
            **tendance
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_tendance: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@prix_bp.route('/historique/<int:arrondissement>', methods=['GET'])
def get_historique_prix(arrondissement: int):
    """
    GET /api/prix/historique/<arrondissement>?type=prix_m2
    
    Retourne l'historique complet des prix (2020-2025)
    
    Query params:
        - type (str): 'prix' ou 'prix_m2', défaut 'prix_m2'
    
    Returns:
        {
            "success": true,
            "data": {
                "arrondissement": 1,
                "type": "prix_m2",
                "historique": [
                    {"annee": 2020, "valeur": 13511},
                    {"annee": 2021, "valeur": 13514},
                    ...
                ]
            }
        }
    """
    try:
        type_prix = request.args.get('type', 'prix_m2', type=str)
        
        # Validation
        if not 1 <= arrondissement <= 20:
            return format_error(f"Arrondissement invalide : {arrondissement}", status=400)
        if type_prix not in ['prix', 'prix_m2']:
            return format_error(f"Type invalide : {type_prix}", status=400)
        
        # Chargement des données
        arr_data = DataLoader.get_arrondissement(arrondissement)
        if not arr_data:
            return format_not_found('Arrondissement', arrondissement)
        
        arr = Arrondissement(arrondissement, arr_data)
        
        # Construction de l'historique
        historique = []
        for annee in range(2020, 2026):
            if type_prix == 'prix_m2':
                valeur = arr.get_prix_m2_median(annee)
            else:
                valeur = arr.get_prix_median(annee)
            
            historique.append({
                'annee': annee,
                'valeur': valeur
            })
        
        return format_response({
            'arrondissement': arrondissement,
            'type': type_prix,
            'historique': historique
        })
    
    except Exception as e:
        logger.error(f"Erreur dans get_historique_prix: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


@prix_bp.route('/comparaison', methods=['GET'])
def comparer_arrondissements():
    """
    GET /api/prix/comparaison?arrondissements=1,2,3&annee=2024&type=prix_m2
    
    Compare les prix de plusieurs arrondissements
    
    Query params:
        - arrondissements (str): Liste d'arrondissements séparés par des virgules (ex: "1,2,3")
        - annee (int): Année de comparaison, défaut 2024
        - type (str): 'prix' ou 'prix_m2', défaut 'prix_m2'
    
    Returns:
        {
            "success": true,
            "data": {
                "annee": 2024,
                "type": "prix_m2",
                "comparaison": [
                    {"arrondissement": 1, "valeur": 12586},
                    {"arrondissement": 2, "valeur": 11444},
                    ...
                ]
            }
        }
    """
    try:
        # Paramètres
        arr_list_str = request.args.get('arrondissements', '1,2,3,4,5')
        annee = request.args.get('annee', 2024, type=int)
        type_prix = request.args.get('type', 'prix_m2', type=str)
        
        # Parse des arrondissements
        try:
            arrondissements = [int(a.strip()) for a in arr_list_str.split(',')]
        except ValueError:
            return format_error("Format invalide pour les arrondissements", status=400)
        
        # Validation
        if not all(1 <= a <= 20 for a in arrondissements):
            return format_error("Un ou plusieurs arrondissements sont invalides", status=400)
        if not 2020 <= annee <= 2025:
            return format_error(f"Année invalide : {annee}", status=400)
        if type_prix not in ['prix', 'prix_m2']:
            return format_error(f"Type invalide : {type_prix}", status=400)
        
        # Construction de la comparaison
        comparaison = []
        for arr_num in arrondissements:
            arr_data = DataLoader.get_arrondissement(arr_num)
            if arr_data:
                arr = Arrondissement(arr_num, arr_data)
                
                if type_prix == 'prix_m2':
                    valeur = arr.get_prix_m2_median(annee)
                else:
                    valeur = arr.get_prix_median(annee)
                
                comparaison.append({
                    'arrondissement': arr_num,
                    'valeur': valeur
                })
        
        # Tri par valeur décroissante
        comparaison.sort(key=lambda x: x['valeur'] if x['valeur'] is not None else 0, reverse=True)
        
        return format_response({
            'annee': annee,
            'type': type_prix,
            'comparaison': comparaison
        })
    
    except Exception as e:
        logger.error(f"Erreur dans comparer_arrondissements: {e}")
        return format_error(f"Erreur interne: {str(e)}", status=500)


# Export du blueprint
__all__ = ['prix_bp']
