/**
 * Client API avec cache léger
 */

class APIClient {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.cache = new Map();
    }

    async request(endpoint) {
        if (this.cache.has(endpoint)) return this.cache.get(endpoint);

        try {
            const url = `${this.baseURL}${endpoint}`;
            log(`🌐 API Request: ${url}`, 'info');
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            const json = await response.json();
            const data = (json && json.success && json.data) ? json.data : json;
            this.cache.set(endpoint, data);
            return data;
        } catch (error) {
            log(`❌ Erreur API ${endpoint}: ${error.message}`, 'error');
            throw error;
        }
    }

    clearCache() { this.cache.clear(); }

    async getAllArrondissements() {
        const response = await this.request('/arrondissements');
        return response.arrondissements || response;
    }

    async getArrondissement(numero) {
        return await this.request(`/arrondissements/${numero}`);
    }

    async getStats() {
        return await this.request('/stats');
    }

    async getHealth() {
        return await this.request('/health');
    }

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
