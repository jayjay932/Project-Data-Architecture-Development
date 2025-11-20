"""
Service de gestion du cache
"""
from typing import Any, Optional, Callable
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service de cache simple en mémoire
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialise le service de cache
        
        Args:
            default_ttl: Durée de vie par défaut du cache en secondes (5 min)
        """
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur depuis le cache
        
        Args:
            key: Clé du cache
            
        Returns:
            Valeur ou None si expiré/inexistant
        """
        if key not in self._cache:
            return None
        
        # Vérifier expiration
        if self._is_expired(key):
            self.delete(key)
            return None
        
        logger.debug(f"Cache hit: {key}")
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Stocke une valeur dans le cache
        
        Args:
            key: Clé du cache
            value: Valeur à stocker
            ttl: Durée de vie en secondes (utilise default_ttl si None)
        """
        self._cache[key] = value
        self._timestamps[key] = {
            'created_at': time.time(),
            'ttl': ttl or self.default_ttl
        }
        logger.debug(f"Cache set: {key} (TTL: {ttl or self.default_ttl}s)")
    
    def delete(self, key: str):
        """
        Supprime une entrée du cache
        
        Args:
            key: Clé à supprimer
        """
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """Vide complètement le cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Cache cleared")
    
    def _is_expired(self, key: str) -> bool:
        """
        Vérifie si une entrée est expirée
        
        Args:
            key: Clé à vérifier
            
        Returns:
            True si expiré
        """
        if key not in self._timestamps:
            return True
        
        ts_info = self._timestamps[key]
        age = time.time() - ts_info['created_at']
        return age > ts_info['ttl']
    
    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur le cache
        
        Returns:
            Dict avec statistiques
        """
        expired = sum(1 for key in self._cache.keys() if self._is_expired(key))
        
        return {
            'size': len(self._cache),
            'expired': expired,
            'active': len(self._cache) - expired
        }


# Instance globale du cache
_cache_instance = None


def get_cache_instance(ttl: int = 300) -> CacheService:
    """
    Récupère l'instance singleton du cache
    
    Args:
        ttl: TTL par défaut
        
    Returns:
        Instance CacheService
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService(default_ttl=ttl)
    return _cache_instance


def cached(ttl: Optional[int] = None, key_prefix: str = ''):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Args:
        ttl: Durée de vie du cache en secondes
        key_prefix: Préfixe pour la clé de cache
        
    Usage:
        @cached(ttl=60, key_prefix='prix')
        def get_prix(arrondissement):
            return expensive_computation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_instance()
            
            # Construire la clé de cache
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Essayer de récupérer depuis le cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Calculer et mettre en cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Exemple d'utilisation
if __name__ == '__main__':
    # Test du cache
    cache = CacheService(default_ttl=5)
    
    cache.set('test', 'valeur', ttl=10)
    print(cache.get('test'))  # 'valeur'
    
    time.sleep(2)
    print(cache.get('test'))  # 'valeur'
    
    print(cache.get_stats())  # {'size': 1, 'expired': 0, 'active': 1}
