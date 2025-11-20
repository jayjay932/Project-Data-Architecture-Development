"""
Schémas de validation pour l'API
"""
from typing import Optional, List
from marshmallow import Schema, fields, validate, ValidationError


class ArrondissementSchema(Schema):
    """Schéma de validation pour un arrondissement"""
    numero = fields.Integer(required=True, validate=validate.Range(min=1, max=20))
    nom = fields.String()


class PrixQuerySchema(Schema):
    """Schéma pour les requêtes de prix"""
    arrondissement = fields.Integer(required=True, validate=validate.Range(min=1, max=20))
    annee = fields.Integer(validate=validate.Range(min=2020, max=2025))
    type = fields.String(validate=validate.OneOf(['prix', 'prix_m2']))


class EvolutionQuerySchema(Schema):
    """Schéma pour les requêtes d'évolution"""
    arrondissement = fields.Integer(required=True, validate=validate.Range(min=1, max=20))
    debut = fields.Integer(required=True, validate=validate.Range(min=2020, max=2024))
    fin = fields.Integer(required=True, validate=validate.Range(min=2021, max=2025))
    type = fields.String(validate=validate.OneOf(['prix', 'prix_m2']))


class ComparaisonQuerySchema(Schema):
    """Schéma pour les requêtes de comparaison"""
    arrondissements = fields.String(required=True)  # Ex: "1,2,3"
    annee = fields.Integer(validate=validate.Range(min=2020, max=2025))
    type = fields.String(validate=validate.OneOf(['prix', 'prix_m2']))


class PollutionQuerySchema(Schema):
    """Schéma pour les requêtes pollution"""
    polluant = fields.String(validate=validate.OneOf(['no2', 'pm10', 'o3']))
    ordre = fields.String(validate=validate.OneOf(['asc', 'desc']))


def validate_request(schema: Schema, data: dict) -> dict:
    """
    Valide les données d'une requête
    
    Args:
        schema: Schéma Marshmallow
        data: Données à valider
        
    Returns:
        Données validées
        
    Raises:
        ValidationError: Si validation échoue
    """
    return schema.load(data)


def get_validation_errors(error: ValidationError) -> dict:
    """
    Formate les erreurs de validation
    
    Args:
        error: Exception ValidationError
        
    Returns:
        Dict formaté des erreurs
    """
    return error.messages
