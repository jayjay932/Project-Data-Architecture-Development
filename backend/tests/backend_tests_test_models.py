"""
Tests unitaires pour les models
"""
import pytest
from backend.models.arrondissement import Arrondissement
from backend.models.prix import PrixModel
from backend.models.logement import LogementModel
from backend.models.transport import TransportModel
from backend.models.pollution import PollutionModel


class TestArrondissement:
    """Tests pour le model Arrondissement"""
    
    def test_creation_arrondissement(self):
        """Test la création d'un arrondissement"""
        data = {
            'Arrondissement': 1,
            'prix_m2_median_2024': 12586,
            'prix_median_2024': 560000
        }
        arr = Arrondissement(1, data)
        assert arr.numero == 1
        assert arr.get_prix_m2_median(2024) == 12586
    
    def test_numero_invalide(self):
        """Test qu'un numéro invalide lève une exception"""
        with pytest.raises(ValueError):
            Arrondissement(25, {})
    
    def test_get_transport(self):
        """Test la récupération des données transport"""
        data = {
            'nb_stations_metro': 7,
            'nb_lignes_metro': 6,
            'lignes_metro': '1, 4, 7, 14'
        }
        arr = Arrondissement(1, data)
        transport = arr.get_transport()
        assert transport['metro']['nb_stations'] == 7
        assert len(transport['metro']['lignes']) == 4


class TestPrixModel:
    """Tests pour PrixModel"""
    
    def test_calculer_evolution(self):
        """Test le calcul d'évolution"""
        result = PrixModel.calculer_evolution(10000, 11000)
        assert result['evolution_pct'] == 10.0
        assert result['tendance'] == 'Forte hausse'
    
    def test_classifier_prix(self):
        """Test la classification des prix"""
        assert PrixModel.classifier_prix(7000) == 'Très abordable'
        assert PrixModel.classifier_prix(15000) == 'Très élevé'


class TestLogementModel:
    """Tests pour LogementModel"""
    
    def test_calculer_indice_mixite(self):
        """Test le calcul de l'indice de mixité"""
        indice = LogementModel.calculer_indice_mixite(200, 1000)
        assert indice == 20.0
    
    def test_classifier_mixite(self):
        """Test la classification de mixité"""
        assert LogementModel.classifier_mixite(25) == 'Élevé (>20%)'
        assert LogementModel.classifier_mixite(15) == 'Moyen (10-20%)'
        assert LogementModel.classifier_mixite(5) == 'Faible (<10%)'


class TestTransportModel:
    """Tests pour TransportModel"""
    
    def test_calculer_score_accessibilite(self):
        """Test le calcul du score d'accessibilité"""
        score = TransportModel.calculer_score_accessibilite(10, 5)
        assert score == 100  # (10*5 + 5*10) = 100
    
    def test_trier_lignes(self):
        """Test le tri des lignes"""
        lignes = ['B', '1', 'A', '14', '4']
        triees = TransportModel.trier_lignes(lignes)
        assert triees == ['1', '4', '14', 'A', 'B']


class TestPollutionModel:
    """Tests pour PollutionModel"""
    
    def test_classifier_no2(self):
        """Test la classification NO2"""
        assert PollutionModel.classifier_no2(30) == 'Bon'
        assert PollutionModel.classifier_no2(60) == 'Moyen'
        assert PollutionModel.classifier_no2(100) == 'Médiocre'
    
    def test_calculer_indice_global(self):
        """Test le calcul de l'indice global"""
        result = PollutionModel.calculer_indice_global(30, 20, 50)
        assert result['qualite'] in ['Bonne', 'Moyenne', 'Médiocre', 'Mauvaise']
        assert 'indice' in result


if __name__ == '__main__':
    pytest.main([__file__])
