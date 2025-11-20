"""
Tests d'intégration pour l'application complète
"""
import pytest
from backend.app import create_app
from backend.services.data_loader import DataLoader


@pytest.fixture
def app():
    """Fixture pour créer l'application"""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """Fixture pour le client de test"""
    return app.test_client()


class TestIntegrationComplete:
    """Tests d'intégration bout-en-bout"""
    
    def test_flux_complet_prix(self, client):
        """Test un flux complet de consultation des prix"""
        # 1. Obtenir la liste des arrondissements
        response = client.get('/api/arrondissements')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['arrondissements']) == 20
        
        # 2. Obtenir les détails du 1er arrondissement
        response = client.get('/api/arrondissements/1')
        assert response.status_code == 200
        
        # 3. Obtenir le prix/m² 2024
        response = client.get('/api/prix/m2/1?annee=2024')
        assert response.status_code == 200
        
        # 4. Obtenir l'évolution
        response = client.get('/api/prix/evolution/1?debut=2020&fin=2024')
        assert response.status_code == 200
    
    def test_flux_complet_logement(self, client):
        """Test un flux complet pour les logements"""
        arr = 1
        
        # Logements sociaux
        response = client.get(f'/api/logements/sociaux/{arr}')
        assert response.status_code == 200
        
        # Typologie
        response = client.get(f'/api/logements/typologie/{arr}')
        assert response.status_code == 200
        
        # Répartition pièces
        response = client.get(f'/api/logements/pieces/{arr}')
        assert response.status_code == 200
    
    def test_comparaison_arrondissements(self, client):
        """Test la comparaison entre plusieurs arrondissements"""
        response = client.get('/api/prix/comparaison?arrondissements=1,2,3&annee=2024')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['comparaison']) == 3
    
    def test_classements(self, client):
        """Test les différents classements"""
        # Transport
        response = client.get('/api/transport/classement?critere=nb_lignes_metro')
        assert response.status_code == 200
        
        # Pollution
        response = client.get('/api/pollution/polluant/no2?ordre=desc')
        assert response.status_code == 200
    
    def test_erreurs_validation(self, client):
        """Test la gestion des erreurs de validation"""
        # Arrondissement invalide
        response = client.get('/api/prix/m2/25')
        assert response.status_code == 400
        
        # Année invalide
        response = client.get('/api/prix/m2/1?annee=2030')
        assert response.status_code == 400
    
    def test_data_loader_integration(self, app):
        """Test l'intégration du DataLoader"""
        with app.app_context():
            # Charger tous les arrondissements
            arrs = DataLoader.get_all_arrondissements()
            assert len(arrs) == 20
            
            # Charger un arrondissement spécifique
            arr1 = DataLoader.get_arrondissement(1)
            assert arr1 is not None
            assert arr1['Arrondissement'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
