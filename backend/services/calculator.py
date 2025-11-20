"""
Service de calculs statistiques et métriques
"""
from typing import List, Dict, Optional, Any
import numpy as np
from scipy import stats


class Calculator:
    """
    Service pour effectuer des calculs statistiques avancés
    """
    
    @staticmethod
    def calculer_statistiques(values: List[float]) -> Dict[str, float]:
        """
        Calcule les statistiques descriptives d'une série
        
        Args:
            values: Liste de valeurs numériques
            
        Returns:
            Dict avec min, max, moyenne, médiane, écart-type, etc.
        """
        if not values:
            return {}
        
        clean_values = [v for v in values if v is not None and not np.isnan(v)]
        
        if not clean_values:
            return {}
        
        return {
            'count': len(clean_values),
            'min': float(np.min(clean_values)),
            'max': float(np.max(clean_values)),
            'mean': float(np.mean(clean_values)),
            'median': float(np.median(clean_values)),
            'std': float(np.std(clean_values)),
            'q25': float(np.percentile(clean_values, 25)),
            'q75': float(np.percentile(clean_values, 75)),
        }
    
    @staticmethod
    def calculer_correlation(x: List[float], y: List[float]) -> Optional[float]:
        """
        Calcule le coefficient de corrélation de Pearson
        
        Args:
            x: Première série de valeurs
            y: Deuxième série de valeurs
            
        Returns:
            Coefficient de corrélation (-1 à 1)
        """
        if len(x) != len(y) or len(x) < 2:
            return None
        
        # Nettoyer les paires (enlever les None/NaN)
        pairs = [(xi, yi) for xi, yi in zip(x, y) 
                 if xi is not None and yi is not None 
                 and not np.isnan(xi) and not np.isnan(yi)]
        
        if len(pairs) < 2:
            return None
        
        x_clean, y_clean = zip(*pairs)
        
        corr, _ = stats.pearsonr(x_clean, y_clean)
        return float(corr)
    
    @staticmethod
    def normaliser(values: List[float], min_val: float = 0, 
                   max_val: float = 1) -> List[float]:
        """
        Normalise une série de valeurs entre min_val et max_val
        
        Args:
            values: Valeurs à normaliser
            min_val: Valeur minimale de sortie
            max_val: Valeur maximale de sortie
            
        Returns:
            Valeurs normalisées
        """
        if not values:
            return []
        
        arr = np.array(values)
        arr_min = np.nanmin(arr)
        arr_max = np.nanmax(arr)
        
        if arr_max == arr_min:
            return [min_val] * len(values)
        
        normalized = ((arr - arr_min) / (arr_max - arr_min)) * (max_val - min_val) + min_val
        return normalized.tolist()
    
    @staticmethod
    def detecter_tendance(series: List[float]) -> Dict[str, Any]:
        """
        Détecte la tendance d'une série temporelle
        
        Args:
            series: Série de valeurs temporelles
            
        Returns:
            Dict avec pente, tendance, et force
        """
        if len(series) < 2:
            return {'tendance': 'Indéterminé', 'pente': 0, 'force': 0}
        
        # Régression linéaire
        x = np.arange(len(series))
        y = np.array(series)
        
        # Enlever les NaN
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 2:
            return {'tendance': 'Indéterminé', 'pente': 0, 'force': 0}
        
        slope, intercept, r_value, _, _ = stats.linregress(x, y)
        
        # Déterminer la tendance
        if abs(slope) < 0.1:
            tendance = 'Stable'
        elif slope > 0:
            if slope > 1:
                tendance = 'Forte hausse'
            else:
                tendance = 'Hausse modérée'
        else:
            if slope < -1:
                tendance = 'Forte baisse'
            else:
                tendance = 'Baisse modérée'
        
        return {
            'tendance': tendance,
            'pente': float(slope),
            'force': float(abs(r_value))  # R² comme mesure de force
        }
    
    @staticmethod
    def calculer_rang_percentile(value: float, all_values: List[float]) -> int:
        """
        Calcule le rang percentile d'une valeur
        
        Args:
            value: Valeur à évaluer
            all_values: Toutes les valeurs de référence
            
        Returns:
            Percentile (0-100)
        """
        if not all_values:
            return 50
        
        clean_values = [v for v in all_values if v is not None and not np.isnan(v)]
        
        if value is None or np.isnan(value):
            return 50
        
        rank = sum(1 for v in clean_values if v <= value)
        percentile = (rank / len(clean_values)) * 100
        
        return int(percentile)
    
    @staticmethod
    def calculer_score_composite(metrics: Dict[str, float], 
                                 weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calcule un score composite pondéré
        
        Args:
            metrics: Dict des métriques {nom: valeur}
            weights: Dict des poids {nom: poids} (optionnel, égal par défaut)
            
        Returns:
            Score composite normalisé (0-100)
        """
        if not metrics:
            return 0.0
        
        if weights is None:
            weights = {k: 1.0 for k in metrics.keys()}
        
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        
        score = sum(metrics.get(k, 0) * weights.get(k, 0) for k in metrics.keys())
        return (score / total_weight)
