"""
Model pour la logique métier de la pollution et qualité de l'air
"""
from typing import Dict, Optional


class PollutionModel:
    """
    Logique métier pour l'analyse de la qualité de l'air
    """
    
    # Seuils OMS (µg/m³)
    SEUILS_NO2 = {'bon': 40, 'moyen': 90, 'mauvais': 150}
    SEUILS_PM10 = {'bon': 20, 'moyen': 50, 'mauvais': 100}
    SEUILS_O3 = {'bon': 100, 'moyen': 160, 'mauvais': 240}
    
    @staticmethod
    def classifier_no2(valeur: float) -> str:
        """
        Classifie le niveau de NO2
        
        Args:
            valeur: Concentration en µg/m³
            
        Returns:
            Catégorie (Bon, Moyen, Médiocre, Mauvais)
        """
        if valeur <= PollutionModel.SEUILS_NO2['bon']:
            return 'Bon'
        elif valeur <= PollutionModel.SEUILS_NO2['moyen']:
            return 'Moyen'
        elif valeur <= PollutionModel.SEUILS_NO2['mauvais']:
            return 'Médiocre'
        else:
            return 'Mauvais'
    
    @staticmethod
    def classifier_pm10(valeur: float) -> str:
        """
        Classifie le niveau de PM10
        
        Args:
            valeur: Concentration en µg/m³
            
        Returns:
            Catégorie (Bon, Moyen, Médiocre, Mauvais)
        """
        if valeur <= PollutionModel.SEUILS_PM10['bon']:
            return 'Bon'
        elif valeur <= PollutionModel.SEUILS_PM10['moyen']:
            return 'Moyen'
        elif valeur <= PollutionModel.SEUILS_PM10['mauvais']:
            return 'Médiocre'
        else:
            return 'Mauvais'
    
    @staticmethod
    def classifier_o3(valeur: float) -> str:
        """
        Classifie le niveau d'ozone
        
        Args:
            valeur: Concentration en µg/m³
            
        Returns:
            Catégorie (Bon, Moyen, Médiocre, Mauvais)
        """
        if valeur <= PollutionModel.SEUILS_O3['bon']:
            return 'Bon'
        elif valeur <= PollutionModel.SEUILS_O3['moyen']:
            return 'Moyen'
        elif valeur <= PollutionModel.SEUILS_O3['mauvais']:
            return 'Médiocre'
        else:
            return 'Mauvais'
    
    @staticmethod
    def calculer_indice_global(no2: float, pm10: float, o3: float) -> Dict[str, any]:
        """
        Calcule un indice global de qualité de l'air
        
        Args:
            no2: Concentration NO2
            pm10: Concentration PM10
            o3: Concentration O3
            
        Returns:
            Dict avec indice et qualité
        """
        # Normaliser chaque polluant (0-100, 100 = mauvais)
        score_no2 = min((no2 / PollutionModel.SEUILS_NO2['mauvais']) * 100, 100)
        score_pm10 = min((pm10 / PollutionModel.SEUILS_PM10['mauvais']) * 100, 100)
        score_o3 = min((o3 / PollutionModel.SEUILS_O3['mauvais']) * 100, 100)
        
        # Indice = pire score
        indice = max(score_no2, score_pm10, score_o3)
        
        # Qualité selon l'indice
        if indice <= 30:
            qualite = 'Bonne'
        elif indice <= 50:
            qualite = 'Moyenne'
        elif indice <= 75:
            qualite = 'Médiocre'
        else:
            qualite = 'Mauvaise'
        
        return {
            'indice': round(indice, 1),
            'qualite': qualite,
            'polluant_principal': max(
                [('NO2', score_no2), ('PM10', score_pm10), ('O3', score_o3)],
                key=lambda x: x[1]
            )[0]
        }
    
    @staticmethod
    def comparer_qualite(arr1_data: Dict, arr2_data: Dict) -> str:
        """
        Compare la qualité de l'air de deux arrondissements
        
        Args:
            arr1_data: Données pollution arrondissement 1
            arr2_data: Données pollution arrondissement 2
            
        Returns:
            Résultat de la comparaison
        """
        indice1 = PollutionModel.calculer_indice_global(
            arr1_data.get('no2', 0),
            arr1_data.get('pm10', 0),
            arr1_data.get('o3', 0)
        )['indice']
        
        indice2 = PollutionModel.calculer_indice_global(
            arr2_data.get('no2', 0),
            arr2_data.get('pm10', 0),
            arr2_data.get('o3', 0)
        )['indice']
        
        if abs(indice1 - indice2) < 5:
            return 'Qualité comparable'
        elif indice1 < indice2:
            return 'Premier arrondissement plus sain'
        else:
            return 'Deuxième arrondissement plus sain'
