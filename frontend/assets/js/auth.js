/**
 * Gestion de session JWT côté frontend
 */

const AuthSession = {
    TOKEN_KEY: 'ude.jwt.token',
    USER_KEY: 'ude.jwt.user',
    TYPE_KEY: 'ude.jwt.type',
    EXPIRES_KEY: 'ude.jwt.expires',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    getUser() {
        const raw = localStorage.getItem(this.USER_KEY);
        if (!raw) return null;

        try {
            return JSON.parse(raw);
        } catch (error) {
            log('⚠️ Session utilisateur illisible, réinitialisation', 'warning');
            this.clearSession();
            return null;
        }
    },

    hasToken() {
        return Boolean(this.getToken());
    },

    saveSession(data) {
        if (!data || !data.token) {
            throw new Error('Session invalide: token manquant');
        }

        localStorage.setItem(this.TOKEN_KEY, data.token);
        localStorage.setItem(this.TYPE_KEY, data.type || 'Bearer');
        localStorage.setItem(this.EXPIRES_KEY, data.expires_in || '');

        if (data.user) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(data.user));
        }
    },

    clearSession() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        localStorage.removeItem(this.TYPE_KEY);
        localStorage.removeItem(this.EXPIRES_KEY);
    },

    getRoleLabel(role) {
        if (role === 'admin') return 'Administrateur';
        if (role === 'viewer') return 'Lecture seule';
        return role || 'Utilisateur';
    },

    getDisplayName() {
        const user = this.getUser();
        if (!user) return 'Session inactive';
        return user.name || user.username || 'Utilisateur';
    },

    getInitial() {
        const user = this.getUser();
        const source = user?.name || user?.username || 'U';
        return source.charAt(0).toUpperCase();
    },

    syncHeaderUI() {
        const chip = document.getElementById('auth-session');
        if (!chip) return;

        const user = this.getUser();
        if (!user) {
            chip.classList.add('hidden');
            return;
        }

        const avatar = document.getElementById('auth-avatar');
        const name = document.getElementById('auth-name');
        const role = document.getElementById('auth-role');

        if (avatar) avatar.textContent = this.getInitial();
        if (name) name.textContent = this.getDisplayName();
        if (role) role.textContent = this.getRoleLabel(user.role);

        chip.classList.remove('hidden');
    },

    attachLogoutHandler() {
        const logoutBtn = document.getElementById('logout-btn');
        if (!logoutBtn || logoutBtn.dataset.bound === 'true') return;

        logoutBtn.addEventListener('click', () => this.logout());
        logoutBtn.dataset.bound = 'true';
    },

    redirectToLogin() {
        window.location.replace('login.html');
    },

    redirectToDashboard() {
        window.location.replace('index.html');
    },

    async requestWithFallback(api, endpoint, options = {}) {
        if (api && typeof api.request === 'function') {
            return api.request(endpoint, options);
        }

        const baseURL = api?.baseURL || 'http://localhost:5000/api';
        const headers = {
            ...(options.auth === false ? {} : this.getToken() ? { Authorization: `Bearer ${this.getToken()}` } : {}),
            ...(options.headers || {})
        };

        const fetchOptions = {
            method: options.method || 'GET',
            headers
        };

        if (options.body !== undefined) {
            fetchOptions.body = JSON.stringify(options.body);
            fetchOptions.headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(`${baseURL}${endpoint}`, fetchOptions);
        const json = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(json?.error?.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        if (json?.success && Object.prototype.hasOwnProperty.call(json, 'data')) {
            return json.data;
        }

        return json;
    },

    async ensureAuthenticated(api, { redirect = true } = {}) {
        const token = this.getToken();
        if (!token) {
            if (redirect) this.redirectToLogin();
            return null;
        }

        try {
            const verification = typeof api?.verifyToken === 'function'
                ? await api.verifyToken()
                : await this.requestWithFallback(api, '/auth/verify');
            let user = this.getUser();

            if (
                !user ||
                user.username !== verification.user ||
                user.role !== verification.role ||
                !user.name
            ) {
                const currentUser = typeof api?.getCurrentUser === 'function'
                    ? await api.getCurrentUser()
                    : await this.requestWithFallback(api, '/auth/me');
                user = {
                    username: currentUser.username || verification.user,
                    role: currentUser.role || verification.role,
                    name: currentUser.name || verification.user
                };
            }

            this.saveSession({
                token,
                type: localStorage.getItem(this.TYPE_KEY) || 'Bearer',
                expires_in: localStorage.getItem(this.EXPIRES_KEY) || '',
                user
            });

            this.syncHeaderUI();
            this.attachLogoutHandler();
            return user;
        } catch (error) {
            log(`🔐 Session expirée ou invalide: ${error.message}`, 'warning');
            this.clearSession();
            this.syncHeaderUI();

            if (redirect) this.redirectToLogin();
            return null;
        }
    },

    async login(api, username, password) {
        const session = typeof api?.login === 'function'
            ? await api.login(username, password)
            : await this.requestWithFallback(api, '/auth/login', {
                method: 'POST',
                body: { username, password },
                auth: false
            });
        this.saveSession(session);
        this.syncHeaderUI();
        this.attachLogoutHandler();
        return session.user;
    },

    logout({ redirect = true } = {}) {
        this.clearSession();
        this.syncHeaderUI();

        if (redirect) {
            this.redirectToLogin();
        }
    }
};

window.AuthSession = AuthSession;
