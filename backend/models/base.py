"""
Classe de base pour tous les models
"""
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
    Classe de base abstraite pour tous les models
    
    Fournit des méthodes communes pour la manipulation de données
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialise le model avec des données
        
        Args:
            data: Dictionnaire contenant les données du model
        """
        self._data = data
        self._validate()
    
    @abstractmethod
    def _validate(self):
        """
        Valide les données du model
        À implémenter dans les classes enfants
        """
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur depuis les données
        
        Args:
            key: Clé à récupérer
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            Valeur associée à la clé
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Définit une valeur dans les données
        
        Args:
            key: Clé à définir
            value: Valeur à associer
        """
        self._data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le model en dictionnaire
        
        Returns:
            Dictionnaire représentant le model
        """
        return self._data.copy()
    
    def update(self, data: Dict[str, Any]):
        """
        Met à jour les données du model
        
        Args:
            data: Dictionnaire avec les nouvelles données
        """
        self._data.update(data)
        self._validate()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}"
