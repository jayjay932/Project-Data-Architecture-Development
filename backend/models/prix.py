"""
Model pour la logique métier des prix immobiliers
"""
from typing import Optional, List, Dict, Any


class PrixModel:
    """
    Logique métier pour les calculs de prix immobiliers
    """
    
    @staticmethod
    def calculer_evolution(prix_debut: float, prix_fin: float) -> Dict[str, Any]:
        """
        Calcule l'évolution entre deux prix
        
        Args:
            prix_debut: Prix de départ
            prix_fin: Prix d'arrivée
            
        Returns:
            Dict avec évolution_pct, variation_absolue, et tendance
        """
        if prix_debut is None or prix_fin is None or prix_debut == 0:
            return {
                'evolution_pct': None,
                'variation_absolue': None,
                'tendance': 'Indéterminé'
            }
        
        evolution_pct = ((prix_fin - prix_debut) / prix_debut) * 100
        variation_absolue = prix_fin - prix_debut
        
        # Déterminer la tendance
        if evolution_pct > 5:
            tendance = 'Forte hausse'
        elif evolution_pct > 2:
            tendance = 'Hausse modérée'
        elif evolution_pct > -2:
            tendance = 'Stable'
        elif evolution_pct > -5:
            tendance = 'Baisse modérée'
        else:
            tendance = 'Forte baisse'
        
        return {
            'evolution_pct': round(evolution_pct, 2),
            'variation_absolue': round(variation_absolue, 2),
            'tendance': tendance
        }
    
    @staticmethod
    def calculer_volatilite(series: List[float]) -> Optional[float]:
        """
        Calcule la volatilité d'une série de prix
        
        Args:
            series: Liste de valeurs
            
        Returns:
            Écart-type de la série
        """
        import numpy as np
        
        if not series or len(series) < 2:
            return None
        
        return float(np.std(series))
    
    @staticmethod
    def detecter_anomalies(prix: float, moyenne: float, ecart_type: float, 
                          seuil: float = 2.0) -> bool:
        """
        Détecte si un prix est une anomalie statistique
        
        Args:
            prix: Prix à tester
            moyenne: Moyenne des prix
            ecart_type: Écart-type des prix
            seuil: Nombre d'écarts-types pour détecter une anomalie
            
        Returns:
            True si anomalie détectée
        """
        if ecart_type == 0:
            return False
        
        z_score = abs((prix - moyenne) / ecart_type)
        return z_score > seuil
    
    @staticmethod
    def calculer_rang_percentile(prix: float, tous_prix: List[float]) -> int:
        """
        Calcule le rang percentile d'un prix
        
        Args:
            prix: Prix à évaluer
            tous_prix: Liste de tous les prix
            
        Returns:
            Percentile (0-100)
        """
        import numpy as np
        
        if not tous_prix:
            return 50
        
        return int(np.percentile(tous_prix, prix))
    
    @staticmethod
    def classifier_prix(prix_m2: float) -> str:
        """
        Classifie un prix/m² en catégorie
        
        Args:
            prix_m2: Prix au m²
            
        Returns:
            Catégorie (Très abordable, Abordable, Moyen, Élevé, Très élevé)
        """
        if prix_m2 < 8000:
            return 'Très abordable'
        elif prix_m2 < 10000:
            return 'Abordable'
        elif prix_m2 < 12000:
            return 'Moyen'
        elif prix_m2 < 14000:
            return 'Élevé'
        else:
            return 'Très élevé'
