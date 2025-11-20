/**
 * Client API
 */

class APIClient {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
    }

    async request(endpoint) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            log(`🌐 API Request: ${url}`, 'info');
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const json = await response.json();
            
            // L'API renvoie {success: true, data: {...}}
            if (json.success && json.data) {
                return json.data;
            }
            
            return json;
        } catch (error) {
            log(`❌ Erreur API ${endpoint}: ${error.message}`, 'error');
            throw error;
        }
    }

    // Récupérer tous les arrondissements
    async getAllArrondissements() {
        const response = await this.request('/arrondissements');
        return response.arrondissements || response;
    }

    // Récupérer un arrondissement spécifique
    async getArrondissement(numero) {
        return await this.request(`/arrondissements/${numero}`);
    }

    // Récupérer les statistiques globales
    async getStats() {
        return await this.request('/stats');
    }

    // Health check
    async getHealth() {
        return await this.request('/health');
    }

    // Vérifier la connexion
    async checkConnection() {
        try {
            await this.getHealth();
            log('✅ Connexion API OK', 'success');
            return true;
        } catch (error) {
            log('❌ Connexion API échouée', 'error');
            return false;
        }
    }
}