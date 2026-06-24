/**
 * Gestion de la page de connexion
 */

let loginApi;

function setLoginStatus(state, text) {
    const status = document.getElementById('auth-api-status');
    if (!status) return;

    status.dataset.state = state;
    status.textContent = text;
}

function setFormMessage(type, message = '') {
    const errorBox = document.getElementById('login-error');
    const successBox = document.getElementById('login-success');

    if (errorBox) {
        errorBox.classList.add('hidden');
        errorBox.textContent = '';
    }

    if (successBox) {
        successBox.classList.add('hidden');
        successBox.textContent = '';
    }

    if (!message) return;

    const target = type === 'error' ? errorBox : successBox;
    if (!target) return;

    target.textContent = message;
    target.classList.remove('hidden');
}

function bindDemoCredentials() {
    const buttons = document.querySelectorAll('.demo-credential');

    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');

            if (usernameInput) usernameInput.value = button.dataset.username || '';
            if (passwordInput) passwordInput.value = button.dataset.password || '';
        });
    });
}

async function probeBackend() {
    try {
        if (typeof loginApi.getServerInfo === 'function') {
            await loginApi.getServerInfo();
        } else {
            const response = await fetch('http://localhost:5000/');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        }
        setLoginStatus('healthy', 'Backend joignable sur localhost:5000');
    } catch (error) {
        setLoginStatus('error', 'Backend injoignable');
        log(`❌ Backend indisponible: ${error.message}`, 'error');
    }
}

async function handleLogin(event) {
    event.preventDefault();

    const submitButton = document.getElementById('login-submit');
    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value || '';

    setFormMessage(null);

    if (!username || !password) {
        setFormMessage('error', 'Nom d’utilisateur et mot de passe requis.');
        return;
    }

    try {
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Connexion en cours...';
        }

        const user = await AuthSession.login(loginApi, username, password);
        setFormMessage('success', `Connexion réussie. Redirection de ${user.name || user.username}...`);
        setLoginStatus('healthy', 'Session JWT active');

        window.setTimeout(() => {
            AuthSession.redirectToDashboard();
        }, 350);
    } catch (error) {
        setFormMessage('error', error.message || 'Connexion impossible.');
        setLoginStatus('warning', 'Tentative de connexion rejetée');
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Se connecter au dashboard';
        }
    }
}

async function initLoginPage() {
    loginApi = new APIClient('http://localhost:5000/api');

    bindDemoCredentials();
    await probeBackend();

    if (AuthSession.hasToken()) {
        const existingUser = await AuthSession.ensureAuthenticated(loginApi, { redirect: false });
        if (existingUser) {
            AuthSession.redirectToDashboard();
            return;
        }
    }

    const form = document.getElementById('login-form');
    if (form) {
        form.addEventListener('submit', handleLogin);
    }

    log('🔐 Page de connexion prête', 'success');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLoginPage);
} else {
    initLoginPage();
}
