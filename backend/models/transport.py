"""
Model pour la logique métier des transports
"""
from typing import List, Dict, Optional


class TransportModel:
    """
    Logique métier pour l'analyse des transports en commun
    """
    
    @staticmethod
    def calculer_score_accessibilite(nb_stations: int, nb_lignes: int) -> float:
        """
        Calcule un score d'accessibilité en transports
        
        Args:
            nb_stations: Nombre de stations de métro
            nb_lignes: Nombre de lignes de métro/RER
            
        Returns:
            Score sur 100
        """
        # Formule: (stations * 5) + (lignes * 10), plafonné à 100
        score = (nb_stations * 5) + (nb_lignes * 10)
        return min(score, 100)
    
    @staticmethod
    def classifier_accessibilite(score: float) -> str:
        """
        Classifie le niveau d'accessibilité
        
        Args:
            score: Score d'accessibilité (0-100)
            
        Returns:
            Catégorie (Excellent, Bon, Moyen, Faible)
        """
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Bon'
        elif score >= 40:
            return 'Moyen'
        else:
            return 'Faible'
    
    @staticmethod
    def trier_lignes(lignes: List[str]) -> List[str]:
        """
        Trie les lignes de métro de manière intelligente
        
        Args:
            lignes: Liste de lignes (ex: ['1', '4', '7', 'A', 'B'])
            
        Returns:
            Liste triée (chiffres d'abord, puis lettres)
        """
        chiffres = sorted([l for l in lignes if l.isdigit()], key=int)
        lettres = sorted([l for l in lignes if l.isalpha()])
        autres = sorted([l for l in lignes if not l.isdigit() and not l.isalpha()])
        
        return chiffres + lettres + autres
    
    @staticmethod
    def calculer_trafic_par_station(trafic_total: int, nb_stations: int) -> Optional[int]:
        """
        Calcule le trafic moyen par station
        
        Args:
            trafic_total: Trafic total annuel
            nb_stations: Nombre de stations
            
        Returns:
            Trafic moyen par station
        """
        if nb_stations == 0:
            return None
        
        return trafic_total // nb_stations
    
    @staticmethod
    def comparer_accessibilite(arr1: Dict, arr2: Dict) -> str:
        """
        Compare l'accessibilité de deux arrondissements
        
        Args:
            arr1: Données du premier arrondissement
            arr2: Données du deuxième arrondissement
            
        Returns:
            Résultat de la comparaison
        """
        score1 = TransportModel.calculer_score_accessibilite(
            arr1.get('nb_stations', 0),
            arr1.get('nb_lignes', 0)
        )
        score2 = TransportModel.calculer_score_accessibilite(
            arr2.get('nb_stations', 0),
            arr2.get('nb_lignes', 0)
        )
        
        diff = abs(score1 - score2)
        
        if diff < 10:
            return 'Accessibilité comparable'
        elif score1 > score2:
            return 'Premier arrondissement mieux desservi'
        else:
            return 'Deuxième arrondissement mieux desservi'
