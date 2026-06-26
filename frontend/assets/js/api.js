/**
 * Client API avec authentification JWT et cache léger
 */
class APIClient {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.cache = new Map();
    }

    // ── Token JWT depuis sessionStorage ─────────────────────
    _getToken() {
        return sessionStorage.getItem('ude_token');
    }

    _getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        const token = this._getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }

    // ── Redirection si token invalide/expiré ─────────────────
    _handleUnauthorized() {
        sessionStorage.removeItem('ude_token');
        sessionStorage.removeItem('ude_user');
        window.location.href = 'login.html';
    }

    // ── Requête principale ───────────────────────────────────
    async request(endpoint) {
        // Cache (sauf endpoints sensibles)
        if (this.cache.has(endpoint)) return this.cache.get(endpoint);

        try {
            const url = `${this.baseURL}${endpoint}`;
            log(`🌐 API Request: ${url}`, 'info');

            const response = await fetch(url, {
                headers: this._getHeaders()
            });

            // Token expiré ou invalide → retour login
            if (response.status === 401) {
                log('🔒 Token invalide ou expiré — redirection login', 'warning');
                this._handleUnauthorized();
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const json = await response.json();
            const data = (json && json.success && json.data) ? json.data : json;

            // Mettre en cache
            this.cache.set(endpoint, data);
            return data;

        } catch (error) {
            log(`❌ Erreur API ${endpoint}: ${error.message}`, 'error');
            throw error;
        }
    }

    clearCache() { this.cache.clear(); }

    // ── Endpoints ────────────────────────────────────────────
    async getAllArrondissements() {
        const response = await this.request('/arrondissements');
        return response?.arrondissements || response;
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