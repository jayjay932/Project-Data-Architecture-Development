"""
Tests pour les controllers (endpoints API)
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    """Fixture pour créer un client de test"""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


class TestPrixController:
    """Tests pour les endpoints de prix"""
    
    def test_get_prix_m2(self, client):
        """Test GET /api/prix/m2/<arrondissement>"""
        response = client.get('/api/prix/m2/1?annee=2024')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'arrondissement' in data['data']
    
    def test_get_prix_m2_invalide(self, client):
        """Test avec arrondissement invalide"""
        response = client.get('/api/prix/m2/25')
        assert response.status_code == 400
    
    def test_get_evolution(self, client):
        """Test GET /api/prix/evolution/<arrondissement>"""
        response = client.get('/api/prix/evolution/1?debut=2020&fin=2024')
        assert response.status_code == 200
        data = response.get_json()
        assert 'evolution_pct' in data['data']


class TestLogementController:
    """Tests pour les endpoints de logements"""
    
    def test_get_logements_sociaux(self, client):
        """Test GET /api/logements/sociaux/<arrondissement>"""
        response = client.get('/api/logements/sociaux/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'apur' in data['data']
    
    def test_get_typologie(self, client):
        """Test GET /api/logements/typologie/<arrondissement>"""
        response = client.get('/api/logements/typologie/1?annee=2024')
        assert response.status_code == 200


class TestTransportController:
    """Tests pour les endpoints de transport"""
    
    def test_get_transport(self, client):
        """Test GET /api/transport/<arrondissement>"""
        response = client.get('/api/transport/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'metro' in data['data']
        assert 'rer' in data['data']


class TestPollutionController:
    """Tests pour les endpoints de pollution"""
    
    def test_get_qualite_air(self, client):
        """Test GET /api/pollution/<arrondissement>"""
        response = client.get('/api/pollution/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'no2_moyen' in data['data']


class TestGeneralEndpoints:
    """Tests pour les endpoints généraux"""
    
    def test_health_check(self, client):
        """Test GET /api/health"""
        response = client.get('/api/health')
        assert response.status_code in [200, 503]
    
    def test_get_all_arrondissements(self, client):
        """Test GET /api/arrondissements"""
        response = client.get('/api/arrondissements')
        assert response.status_code == 200
        data = response.get_json()
        assert 'arrondissements' in data['data']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
