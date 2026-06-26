/**
 * Point d'entrée — Urban Data Explorer
 * Avec vérification JWT au démarrage
 */

let api, map, ui, comparateur;
let currentMetric = 'prix_m2_median_2024';
let currentYear = '2024';

async function initApp() {
    try {
        // ── Vérification authentification ────────────────────
        const token = sessionStorage.getItem('ude_token');
        const user  = JSON.parse(sessionStorage.getItem('ude_user') || 'null');

        if (!token) {
            log('🔒 Pas de token — redirection login', 'warning');
            window.location.href = 'login.html';
            return;
        }

        // Afficher le nom de l'utilisateur dans le header
        const userEl = document.getElementById('header-user');
        if (userEl && user) {
            userEl.textContent = `👤 ${user.name}`;
        }

        log('🚀 Démarrage Urban Data Explorer...', 'info');

        api = new APIClient('http://localhost:5000/api');

        showLoading();

        // Vérifier la connexion API (envoie le token automatiquement)
        const connected = await api.checkConnection();

        if (!connected) {
            hideLoading();
            alert('Impossible de se connecter à l\'API backend.\nVérifie que le serveur tourne sur http://localhost:5000');
            return;
        }

        ui = new UI(api);

        comparateur = new Comparateur(api, ui);
        comparateur.init();

        map = new ParisMap('map', api);
        await map.init();

        forceUpdateKpiFromMap();

        setupEventListeners();

        await ui.updateKpiCards?.();
        await ui.updateStatsPanel(currentMetric);

        if (map && typeof map.selectArrondissement === 'function') {
            map.selectArrondissement(12);
        }

        await ui.showDetailPanel(12);

        hideLoading();

        log('✅ Application prête', 'success');

    } catch (error) {
        hideLoading();
        log(`❌ Erreur initialisation: ${error.message}`, 'error');
        alert(`Erreur au démarrage :\n${error.message}`);
    }
}

function setupEventListeners() {
    const refreshBtn  = document.getElementById('refresh-btn');
    const metricSelect = document.getElementById('metric-select');
    const yearSelect   = document.getElementById('year-select');

    if (refreshBtn)   refreshBtn.addEventListener('click', handleRefresh);

    if (metricSelect) {
        metricSelect.addEventListener('change', async (e) => {
            currentMetric = e.target.value;
            await handleRefresh(false);
        });
    }

    if (yearSelect) {
        yearSelect.addEventListener('change', async (e) => {
            currentYear = e.target.value;
            await handleRefresh(false);
        });
    }

    window.addEventListener('arrondissement-selected', async (e) => {
        await ui.showDetailPanel(e.detail.numero);
    });

    window.addEventListener('resize', debounce(() => {
        if (map && map.map) map.map.resize();
    }, 180));
}

async function handleRefresh(withLoader = true) {
    try {
        if (withLoader) showLoading();

        await map.updateMetric(currentMetric, currentYear);
        await ui.updateStatsPanel(currentMetric);

        if (ui.currentArrondissement) {
            await ui.showDetailPanel(ui.currentArrondissement);
        }

        if (withLoader) hideLoading();
    } catch (error) {
        if (withLoader) hideLoading();
        log(`❌ Erreur rafraîchissement: ${error.message}`, 'error');
    }
}

// ── Déconnexion ──────────────────────────────────────────────
function logout() {
    sessionStorage.removeItem('ude_token');
    sessionStorage.removeItem('ude_user');
    window.location.href = 'login.html';
}

// ── Erreurs globales ─────────────────────────────────────────
window.addEventListener('error', (e) => {
    log(`❌ Erreur globale: ${e.error || e.message}`, 'error');
});

window.addEventListener('unhandledrejection', (e) => {
    log(`❌ Promise rejetée: ${e.reason}`, 'error');
});

// ── Démarrage ────────────────────────────────────────────────
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// ── KPI depuis map.data ──────────────────────────────────────
function forceUpdateKpiFromMap() {
    if (!map || !map.data || !(map.data instanceof Map)) {
        console.warn('❌ map.data indisponible pour les KPI');
        return;
    }

    const rows = Array.from(map.data.values())
        .map(item => {
            if (!item) return null;
            if (item.data && typeof item.data === 'object') return item.data;
            if (item.arrondissement && typeof item.arrondissement === 'object') return item.arrondissement;
            return item;
        })
        .filter(Boolean);

    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    const num = (value) => {
        if (value === null || value === undefined || value === '') return null;
        const n = Number(String(value).replace(/\s/g,'').replace(',','.').replace('€','').replace('%',''));
        return Number.isFinite(n) ? n : null;
    };

    const firstNumber = (row, keys) => {
        for (const key of keys) {
            const value = num(row[key]);
            if (value !== null) return value;
        }
        return 0;
    };

    const formatShort = (value) => {
        if (value >= 1000000) return `${(value/1000000).toLocaleString('fr-FR',{maximumFractionDigits:1})}M`;
        if (value >= 1000) return `${(value/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})}k`;
        return Math.round(value).toLocaleString('fr-FR');
    };

    const logements = rows.reduce((sum, row) => sum + firstNumber(row, [
        'nb_logements_2022','logements_2022','nb_logements','nb_appartements_2024'
    ]), 0);

    const prices = rows
        .map(row => firstNumber(row, ['prix_m2_median_2024','prix_m2_moyen_2024','prix_m2_median','prix_m2']))
        .filter(v => v > 0);

    setText('kpi-arrondissements', rows.length || 20);
    if (logements > 0) setText('kpi-logements', formatShort(logements));
    if (prices.length > 0) {
        const avg = prices.reduce((s,v) => s+v, 0) / prices.length;
        setText('kpi-marche', `${Math.round(avg).toLocaleString('fr-FR')} €/m²`);
    }
}

console.log('%cUrban Data Explorer', 'font-size:18px;font-weight:bold;color:#c9a84c;');