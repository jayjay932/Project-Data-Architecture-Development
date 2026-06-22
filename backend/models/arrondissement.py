"""
Model principal représentant un arrondissement de Paris
"""
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Arrondissement:
    """
    Représente un arrondissement de Paris avec toutes ses données
    """
    
    def __init__(self, numero: int, data: Dict[str, Any]):
        """
        Initialise un arrondissement
        
        Args:
            numero: Numéro de l'arrondissement (1-20)
            data: Dictionnaire contenant toutes les données brutes
        """
        if not 1 <= numero <= 20:
            raise ValueError(f"Numéro d'arrondissement invalide : {numero}")
        
        self.numero = numero
        self._data = data
    
    # ========================================================================
    # PROPRIÉTÉS DE BASE
    # ========================================================================
    
    @property
    def raw_data(self) -> Dict[str, Any]:
        """Retourne les données brutes"""
        return self._data
    
    # ========================================================================
    # PRIX ET MARCHÉ
    # ========================================================================
    
    def get_prix_m2_median(self, annee: int) -> Optional[float]:
        """
        Retourne le prix/m² médian pour une année donnée
        
        Args:
            annee: Année (2020-2025)
            
        Returns:
            Prix/m² médian ou None si non disponible
        """
        key = f'prix_m2_median_{annee}'
        return self._data.get(key)
    
    def get_prix_median(self, annee: int) -> Optional[float]:
        """
        Retourne le prix médian des ventes pour une année donnée
        
        Args:
            annee: Année (2020-2025)
            
        Returns:
            Prix médian ou None si non disponible
        """
        key = f'prix_median_{annee}'
        return self._data.get(key)
    
    def get_nb_ventes(self, annee: int) -> Optional[int]:
        """
        Retourne le nombre de ventes pour une année donnée
        
        Args:
            annee: Année (2020-2025)
            
        Returns:
            Nombre de ventes ou None si non disponible
        """
        key = f'nb_ventes_{annee}'
        value = self._data.get(key)
        return int(value) if value is not None else None
    
    def get_evolution_prix(self, annee_debut: int, annee_fin: int) -> Optional[float]:
        """
        Calcule l'évolution des prix entre deux années
        
        Args:
            annee_debut: Année de début
            annee_fin: Année de fin
            
        Returns:
            Évolution en % ou None si données manquantes
        """
        key = f'evolution_prix_{annee_debut}_{annee_fin}_pct'
        return self._data.get(key)
    
    def get_evolution_prix_m2(self, annee_debut: int, annee_fin: int) -> Optional[float]:
        """
        Calcule l'évolution des prix/m² entre deux années
        
        Args:
            annee_debut: Année de début
            annee_fin: Année de fin
            
        Returns:
            Évolution en % ou None si données manquantes
        """
        key = f'evolution_prix_m2_{annee_debut}_{annee_fin}_pct'
        return self._data.get(key)
    
    def get_tendance_prix(self) -> Dict[str, Any]:
        """
        Retourne les informations de tendance du marché
        
        Returns:
            Dictionnaire avec tendance, évolution moyenne et volatilité
        """
        return {
            'tendance': self._data.get('tendance_prix_m2'),
            'evolution_annuelle_moyenne_pct': self._data.get('evolution_annuelle_moyenne_pct'),
            'volatilite': self._data.get('volatilite_prix_m2')
        }
    
    # ========================================================================
    # LOGEMENTS SOCIAUX
    # ========================================================================
    
    def get_logements_sociaux_apur(self) -> Dict[str, Any]:
        """
        Retourne les données APUR sur les logements sociaux
        
        Returns:
            Dictionnaire avec nombre et pourcentage
        """
        return {
            'nb_logements_sociaux': self._data.get('nb_logements_sociaux_apur'),
            'part_pct': self._data.get('part_logements_sociaux_apur_pct')
        }
    
    def get_estimation_logement_social(self) -> Optional[str]:
        """
        Retourne l'estimation du niveau de logement social
        
        Returns:
            Catégorie (Élevé/Moyen/Faible) ou None
        """
        return self._data.get('estimation_logement_social_pct')
    
    # ========================================================================
    # TYPOLOGIE DES LOGEMENTS
    # ========================================================================
    
    def get_repartition_pieces(self, annee: int) -> Dict[str, Any]:
        """
        Retourne la répartition par nombre de pièces pour une année
        
        Args:
            annee: Année (2020-2025)
            
        Returns:
            Dictionnaire avec T1, T2, T3, T4, T5plus
        """
        result = {}
        for type_logement in ['T1', 'T2', 'T3', 'T4', 'T5plus']:
            nb_key = f'nb_{type_logement}_{annee}'
            pct_key = f'pct_{type_logement}_{annee}'
            
            result[type_logement] = {
                'nombre': self._data.get(nb_key),
                'pourcentage': self._data.get(pct_key)
            }
        
        return result
    
    def get_repartition_types(self, annee: int) -> Dict[str, Any]:
        """
        Retourne la répartition par type de local
        
        Args:
            annee: Année (2020-2025)
            
        Returns:
            Dictionnaire avec appartements, maisons, etc.
        """
        result = {}
        
        for type_local in ['appartement', 'maison', 'dependance', 'local_industriel_commercial_ou_assimile']:
            nb_key = f'nb_{type_local}_{annee}'
            pct_key = f'pct_{type_local}_{annee}'
            
            nb = self._data.get(nb_key)
            pct = self._data.get(pct_key)
            
            if nb is not None or pct is not None:
                result[type_local] = {
                    'nombre': nb,
                    'pourcentage': pct
                }
        
        # Type dominant par année
        type_dominant_key = f'type_dominant_{annee}'
        result['type_dominant'] = self._data.get(type_dominant_key)
        
        return result
    
    def get_synthese_typologie_2024(self) -> Dict[str, Any]:
        """
        Retourne une synthèse de la typologie en 2024
        
        Returns:
            Dictionnaire avec synthèse appartements/maisons
        """
        return {
            'nb_appartements': self._data.get('nb_appartements_2024'),
            'nb_maisons': self._data.get('nb_maisons_2024'),
            'pct_appartements': self._data.get('pct_appartements'),
            'nb_pieces_moyen': self._data.get('nb_pieces_moyen')
        }
    
    # ========================================================================
    # TRANSPORT
    # ========================================================================
    
    def get_transport(self) -> Dict[str, Any]:
        """
        Retourne toutes les données de transport
        
        Returns:
            Dictionnaire avec métro et RER
        """
        return {
            'metro': {
                'nb_stations': self._data.get('nb_stations_metro'),
                'trafic_total': self._data.get('trafic_total_metro'),
                'nb_lignes': self._data.get('nb_lignes_metro'),
                'lignes': self._parse_lignes(self._data.get('lignes_metro'))
            },
            'rer': {
                'nb_lignes': self._data.get('nb_lignes_rer'),
                'lignes': self._parse_lignes(self._data.get('lignes_rer'))
            }
        }
    
    def _parse_lignes(self, lignes_str: Optional[str]) -> List[str]:
        """Parse une chaîne de lignes séparées par des virgules"""
        if not lignes_str:
            return []
        return [l.strip() for l in str(lignes_str).split(',')]
    
    # ========================================================================
    # POLLUTION / QUALITÉ DE L'AIR
    # ========================================================================
    
    def get_qualite_air(self) -> Dict[str, Any]:
        """
        Retourne les données de qualité de l'air
        
        Returns:
            Dictionnaire avec polluants et qualité dominante
        """
        return {
            'no2_moyen': self._data.get('no2_moyen'),
            'pm10_moyen': self._data.get('pm10_moyen'),
            'o3_moyen': self._data.get('o3_moyen'),
            'qualite_dominante': self._data.get('qualite_air_dominante')
        }
    
    # ========================================================================
    # DÉMOGRAPHIE — MIS À JOUR avec données INSEE 2022 + revenus
    # ========================================================================
    
    def get_demographie(self) -> Dict[str, Any]:
        """
        Retourne les données démographiques réelles (INSEE 2022)
        
        Returns:
            Dictionnaire avec population, ménages, logements, densité, revenus
        """
        return {
            'population_2022': self._data.get('population_2022'),
            'nb_menages_2022': self._data.get('nb_menages_2022'),
            'nb_logements_2022': self._data.get('nb_logements_2022'),
            'superficie_km2': self._data.get('superficie_km2'),
            'densite_pop_km2': self._data.get('densite_pop_km2'),
            'revenu_median': self._data.get('revenu_median'),
            'prix_m2_stats_2020': self._data.get('prix_m2_stats_2020')
        }
    
    # ========================================================================
    # INDICATEURS COMPOSITES — NOUVEAU
    # ========================================================================
    
    def get_indicateurs_composites(self) -> Dict[str, Any]:
        """
        Retourne les 4 indicateurs composites calculés
        
        Returns:
            Dictionnaire avec les 4 indices (score 0-10)
            - indice_accessibilite     : accessibilité prix vs revenus (10 = très accessible)
            - indice_tension_sociale   : fracture sociale prix vs logements sociaux (10 = forte fracture)
            - indice_attractivite      : attractivité transport + prix (10 = très attractif)
            - indice_pression_immo     : pression immobilière marché (10 = forte pression)
            - ratio_effort_achat       : nb années de revenu pour acheter 50m²
        """
        return {
            'indice_accessibilite': self._data.get('indice_accessibilite'),
            'indice_tension_sociale': self._data.get('indice_tension_sociale'),
            'indice_attractivite': self._data.get('indice_attractivite'),
            'indice_pression_immo': self._data.get('indice_pression_immo'),
            'ratio_effort_achat': self._data.get('ratio_effort_achat')
        }
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def to_dict(self, include_all: bool = False) -> Dict[str, Any]:
        """
        Convertit l'arrondissement en dictionnaire
        
        Args:
            include_all: Si True, inclut toutes les données brutes
            
        Returns:
            Dictionnaire représentant l'arrondissement
        """
        if include_all:
            return {
                'numero': self.numero,
                **self._data
            }
        
        # Version simplifiée avec les données principales
        return {
            'numero': self.numero,
            'prix_m2_median_2024': self.get_prix_m2_median(2024),
            'prix_median_2024': self.get_prix_median(2024),
            'logements_sociaux': self.get_logements_sociaux_apur(),
            'transport': self.get_transport(),
            'qualite_air': self.get_qualite_air(),
            'demographie': self.get_demographie(),
            'indicateurs': self.get_indicateurs_composites()
        }
    
    def __repr__(self) -> str:
        return f"<Arrondissement {self.numero}>"
    
    def __str__(self) -> str:
        return f"Arrondissement {self.numero} de Paris"