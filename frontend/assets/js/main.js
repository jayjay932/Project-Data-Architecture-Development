/**
 * Point d'entrée principal de l'application
 */

// Variables globales
let api, map, ui, comparateur;
let currentMetric = 'prix_m2_median_2024';
let currentYear = '2024';

function setApiStatus(state, text) {
    const status = document.getElementById('api-status');
    const label = document.getElementById('api-status-label');

    if (status) status.dataset.state = state;
    if (label) label.textContent = text;
}

/**
 * Initialise l'application
 */
async function initApp() {
    try {
        log('🚀 Démarrage de l\'application...', 'info');

        api = new APIClient('http://localhost:5000/api');

        const currentUser = await AuthSession.ensureAuthenticated(api, { redirect: true });
        if (!currentUser) return;

        setApiStatus('loading', `Session active · ${currentUser.username}`);

        showLoading();
        const connection = await api.checkConnection();

        if (!connection.ok) {
            hideLoading();
            setApiStatus('degraded', 'Backend disponible · SQL indisponible');
            alert(
                `⚠️ Authentification réussie, mais le dashboard de données n'est pas prêt.\n\n${connection.message}\n\nDémarre PostgreSQL puis recharge la page.`
            );
            return;
        }

        setApiStatus('healthy', 'API locale · PostgreSQL connecté');

        ui = new UI(api);
        comparateur = new Comparateur(api, ui);
        comparateur.init();

        map = new ParisMap('map', api);
        await map.init();

        hideLoading();

        map.updateLegend();
        await ui.updateStatsPanel(currentMetric);
        initEventListeners();

        log('✅ Application prête !', 'success');
    } catch (error) {
        hideLoading();
        setApiStatus('error', 'Erreur de démarrage');
        log(`❌ Erreur initialisation: ${error.message}`, 'error');
        alert(`Erreur d'initialisation:\n${error.message}\n\nVérifiez la console (F12) pour plus de détails.`);
    }
}

/**
 * Initialise tous les écouteurs d'événements
 */
function initEventListeners() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }

    const metricSelect = document.getElementById('metric-select');
    if (metricSelect) {
        metricSelect.addEventListener('change', (e) => {
            currentMetric = e.target.value;
            ui.updateStatsPanel(currentMetric);
        });
    }

    const yearSelect = document.getElementById('year-select');
    if (yearSelect) {
        yearSelect.addEventListener('change', (e) => {
            currentYear = e.target.value;
        });
    }

    window.addEventListener('arrondissement-selected', (e) => {
        const numero = e.detail.numero;
        ui.showDetailPanel(numero);
    });

    window.addEventListener('resize', debounce(() => {
        if (map && map.map) {
            map.map.resize();
        }
    }, 250));

    log('✅ Écouteurs d\'événements initialisés', 'success');
}

/**
 * Gère le rafraîchissement de la carte
 */
async function handleRefresh() {
    try {
        showLoading();

        log(`🔄 Rafraîchissement: ${currentMetric}, ${currentYear}`, 'info');

        await map.updateMetric(currentMetric, currentYear);
        await ui.updateStatsPanel(currentMetric);

        hideLoading();
        log('✅ Carte rafraîchie', 'success');
    } catch (error) {
        hideLoading();
        log(`❌ Erreur rafraîchissement: ${error.message}`, 'error');
        alert(`Erreur lors du rafraîchissement:\n${error.message}`);
    }
}

window.addEventListener('error', (event) => {
    log(`❌ Erreur globale: ${event.error}`, 'error');
    console.error('Stack trace:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    log(`❌ Promise rejetée: ${event.reason}`, 'error');
    console.error('Raison:', event.reason);
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

console.log('%cUrban Data Explorer — Paris', 'font-size: 20px; font-weight: bold; color: #0f172a;');
console.log('%cSession JWT requise pour accéder au dashboard', 'color: #2563eb;');
console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #94a3b8;');
