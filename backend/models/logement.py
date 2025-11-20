"""
Model pour la logique métier des logements
"""
from typing import Dict, List, Optional


class LogementModel:
    """
    Logique métier pour la typologie et analyse des logements
    """
    
    TYPOLOGIES = ['T1', 'T2', 'T3', 'T4', 'T5plus']
    TYPES_LOCAUX = ['appartement', 'maison', 'dependance', 'local_industriel_commercial_ou_assimile']
    
    @staticmethod
    def calculer_indice_mixite(nb_logements_sociaux: int, 
                               nb_logements_total: int) -> Optional[float]:
        """
        Calcule l'indice de mixité sociale
        
        Args:
            nb_logements_sociaux: Nombre de logements sociaux
            nb_logements_total: Nombre total de logements
            
        Returns:
            Pourcentage de logements sociaux
        """
        if nb_logements_total == 0:
            return None
        
        return (nb_logements_sociaux / nb_logements_total) * 100
    
    @staticmethod
    def classifier_mixite(pourcentage_social: float) -> str:
        """
        Classifie le niveau de mixité sociale
        
        Args:
            pourcentage_social: Pourcentage de logements sociaux
            
        Returns:
            Catégorie (Élevé, Moyen, Faible)
        """
        if pourcentage_social >= 20:
            return 'Élevé (>20%)'
        elif pourcentage_social >= 10:
            return 'Moyen (10-20%)'
        else:
            return 'Faible (<10%)'
    
    @staticmethod
    def calculer_repartition_pieces(data: Dict[str, int]) -> Dict[str, float]:
        """
        Calcule la répartition en pourcentages par nombre de pièces
        
        Args:
            data: Dict avec nb_T1, nb_T2, etc.
            
        Returns:
            Dict avec les pourcentages
        """
        total = sum(data.values())
        if total == 0:
            return {k: 0.0 for k in data.keys()}
        
        return {k: (v / total) * 100 for k, v in data.items()}
    
    @staticmethod
    def typologie_dominante(repartition: Dict[str, float]) -> str:
        """
        Détermine la typologie dominante
        
        Args:
            repartition: Dict avec les pourcentages par typologie
            
        Returns:
            Typologie la plus représentée
        """
        if not repartition:
            return 'Indéterminé'
        
        return max(repartition.items(), key=lambda x: x[1])[0]
    
    @staticmethod
    def calculer_surface_moyenne(nb_pieces_moyen: float) -> float:
        """
        Estime la surface moyenne en fonction du nombre de pièces moyen
        
        Args:
            nb_pieces_moyen: Nombre moyen de pièces
            
        Returns:
            Surface estimée en m²
        """
        # Estimation: ~25m² par pièce + 15m² de base
        return (nb_pieces_moyen * 25) + 15
