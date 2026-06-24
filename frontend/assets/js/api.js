/**
 * Client API
 */

class APIClient {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.rootURL = baseURL.replace(/\/api\/?$/, '');
    }

    getAuthHeaders() {
        const token = window.AuthSession?.getToken?.();
        if (!token) return {};

        return {
            Authorization: `Bearer ${token}`
        };
    }

    async request(endpoint, options = {}) {
        const {
            method = 'GET',
            body,
            headers = {},
            auth = true
        } = options;

        const url = `${this.baseURL}${endpoint}`;
        const finalHeaders = {
            ...headers,
            ...(auth ? this.getAuthHeaders() : {})
        };

        const requestOptions = {
            method,
            headers: finalHeaders
        };

        if (body !== undefined) {
            requestOptions.body = JSON.stringify(body);
            requestOptions.headers['Content-Type'] = 'application/json';
        }

        try {
            log(`🌐 API Request: ${method} ${url}`, 'info');

            const response = await fetch(url, requestOptions);
            const json = await response.json().catch(() => null);

            if (!response.ok) {
                const message = json?.error?.message || `HTTP ${response.status}: ${response.statusText}`;
                const error = new Error(message);
                error.status = response.status;
                error.code = json?.error?.code || null;
                error.payload = json;
                throw error;
            }

            if (json?.success && Object.prototype.hasOwnProperty.call(json, 'data')) {
                return json.data;
            }

            return json;
        } catch (error) {
            log(`❌ Erreur API ${endpoint}: ${error.message}`, 'error');
            throw error;
        }
    }

    async getServerInfo() {
        const response = await fetch(`${this.rootURL}/`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { username, password },
            auth: false
        });
    }

    async verifyToken() {
        return this.request('/auth/verify');
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async refreshToken() {
        return this.request('/auth/refresh', {
            method: 'POST'
        });
    }

    // Récupérer tous les arrondissements
    async getAllArrondissements() {
        const response = await this.request('/arrondissements');
        return response.arrondissements || response;
    }

    // Récupérer un arrondissement spécifique
    async getArrondissement(numero) {
        return this.request(`/arrondissements/${numero}`);
    }

    // Récupérer les statistiques globales
    async getStats() {
        return this.request('/stats');
    }

    // Health check
    async getHealth() {
        return this.request('/health');
    }

    // Vérifier la connexion données
    async checkConnection() {
        try {
            await this.getHealth();
            log('✅ Connexion API + SQL OK', 'success');
            return {
                ok: true,
                message: 'API et base SQL disponibles'
            };
        } catch (error) {
            log(`❌ Vérification backend échouée: ${error.message}`, 'error');
            return {
                ok: false,
                message: error.message,
                status: error.status || null
            };
        }
    }
}
