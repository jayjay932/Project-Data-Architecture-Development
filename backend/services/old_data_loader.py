"""
Service de chargement des données depuis la couche Gold
"""
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Service singleton pour charger et mettre en cache les données Gold"""
    
    _instance = None
    _data_cache: Optional[pd.DataFrame] = None
    _data_path: Optional[Path] = None
    
    def __new__(cls, data_path: Path = None):
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
            if data_path:
                cls._data_path = data_path
        return cls._instance
    
    @classmethod
    def load_data(cls, force_reload: bool = False) -> pd.DataFrame:
        """
        Charge le CSV Gold avec mise en cache
        
        Args:
            force_reload: Force le rechargement des données
            
        Returns:
            DataFrame contenant toutes les données
        """
        if cls._data_cache is None or force_reload:
            if cls._data_path is None:
                raise ValueError("Le chemin des données n'a pas été configuré")
            
            logger.info(f"Chargement des données depuis {cls._data_path}")
            
            try:
                cls._data_cache = pd.read_csv(
                    cls._data_path,
                    sep=';',
                    low_memory=False
                )
                logger.info(f"Données chargées : {len(cls._data_cache)} arrondissements")
            except FileNotFoundError:
                logger.error(f"Fichier non trouvé : {cls._data_path}")
                raise
            except Exception as e:
                logger.error(f"Erreur lors du chargement des données : {e}")
                raise
        
        return cls._data_cache
    
    @classmethod
    def get_arrondissement(cls, numero: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'un arrondissement spécifique
        
        Args:
            numero: Numéro de l'arrondissement (1-20)
            
        Returns:
            Dictionnaire contenant les données ou None si non trouvé
        """
        if not 1 <= numero <= 20:
            logger.warning(f"Numéro d'arrondissement invalide : {numero}")
            return None
        
        df = cls.load_data()
        row = df[df['Arrondissement'] == numero]
        
        if row.empty:
            logger.warning(f"Arrondissement {numero} non trouvé dans les données")
            return None
        
        # Convertir en dict et remplacer NaN par None
        data = row.iloc[0].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in data.items()}
    
    @classmethod
    def get_all_arrondissements(cls) -> List[Dict[str, Any]]:
        """
        Récupère les données de tous les arrondissements
        
        Returns:
            Liste de dictionnaires contenant les données
        """
        df = cls.load_data()
        records = df.to_dict('records')
        
        # Remplacer NaN par None dans tous les enregistrements
        return [
            {k: (None if pd.isna(v) else v) for k, v in record.items()}
            for record in records
        ]
    
    @classmethod
    def get_arrondissements_by_criteria(
        cls,
        prix_min: Optional[float] = None,
        prix_max: Optional[float] = None,
        annee: int = 2024
    ) -> List[Dict[str, Any]]:
        """
        Filtre les arrondissements selon des critères
        
        Args:
            prix_min: Prix/m² minimum
            prix_max: Prix/m² maximum
            annee: Année de référence
            
        Returns:
            Liste des arrondissements correspondants
        """
        df = cls.load_data()
        
        # Filtrer par prix/m²
        prix_col = f'prix_m2_median_{annee}'
        if prix_col in df.columns:
            if prix_min is not None:
                df = df[df[prix_col] >= prix_min]
            if prix_max is not None:
                df = df[df[prix_col] <= prix_max]
        
        records = df.to_dict('records')
        return [
            {k: (None if pd.isna(v) else v) for k, v in record.items()}
            for record in records
        ]
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Retourne la liste des noms de colonnes disponibles"""
        df = cls.load_data()
        return df.columns.tolist()
    
    @classmethod
    def get_stats_summary(cls) -> Dict[str, Any]:
        """
        Retourne un résumé statistique des données
        
        Returns:
            Dictionnaire avec des statistiques globales
        """
        df = cls.load_data()
        
        return {
            'nb_arrondissements': len(df),
            'colonnes': len(df.columns),
            'annees_disponibles': [2020, 2021, 2022, 2023, 2024, 2025],
            'prix_m2_moyen_2024': float(df['prix_m2_median_2024'].mean()) if 'prix_m2_median_2024' in df.columns else None,
            'prix_m2_min_2024': float(df['prix_m2_median_2024'].min()) if 'prix_m2_median_2024' in df.columns else None,
            'prix_m2_max_2024': float(df['prix_m2_median_2024'].max()) if 'prix_m2_median_2024' in df.columns else None,
        }


# Fonction helper pour initialiser le service
def initialize_data_loader(data_path: Path):
    """Initialise le DataLoader avec le chemin des données"""
    DataLoader._data_path = data_path
    logger.info("DataLoader initialisé")
