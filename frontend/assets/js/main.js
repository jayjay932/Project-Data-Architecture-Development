/**
 * Point d'entrée principal de l'application
 */

// Variables globales
let api, map, ui, comparateur;
let currentMetric = 'prix_m2_median_2024';
let currentYear = '2024';

/**
 * Initialise l'application
 */
async function initApp() {
    try {
        log('🚀 Démarrage de l\'application...', 'info');
        
        // Initialiser l'API
        api = new APIClient('http://localhost:5000/api');
        
        // Vérifier la connexion
        showLoading();
        const connected = await api.checkConnection();
        
        if (!connected) {
            hideLoading();
            alert('❌ Impossible de se connecter à l\'API backend.\n\nVérifiez que le serveur est démarré sur http://localhost:5000');
            return;
        }
        
        // Initialiser l'UI
        ui = new UI(api);
        
        // Initialiser le comparateur
        comparateur = new Comparateur(api, ui);
        comparateur.init();
        
        // Initialiser la carte
        map = new ParisMap('map', api);
        await map.init();
        
        hideLoading();
        
        // Mettre à jour la légende initiale
        map.updateLegend();
        
        // Mettre à jour les stats initiales
        await ui.updateStatsPanel(currentMetric);
        
        // Initialiser les écouteurs
        initEventListeners();
        
        log('✅ Application prête !', 'success');
        
    } catch (error) {
        hideLoading();
        log(`❌ Erreur initialisation: ${error.message}`, 'error');
        alert(`Erreur d'initialisation:\n${error.message}\n\nVérifiez la console (F12) pour plus de détails.`);
    }
}

/**
 * Initialise tous les écouteurs d'événements
 */
function initEventListeners() {
    // Bouton de rafraîchissement
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }
    
    // Sélection de métrique
    const metricSelect = document.getElementById('metric-select');
    if (metricSelect) {
        metricSelect.addEventListener('change', (e) => {
            currentMetric = e.target.value;
            ui.updateStatsPanel(currentMetric);
        });
    }
    
    // Sélection d'année
    const yearSelect = document.getElementById('year-select');
    if (yearSelect) {
        yearSelect.addEventListener('change', (e) => {
            currentYear = e.target.value;
        });
    }
    
    // Clic sur arrondissement
    window.addEventListener('arrondissement-selected', (e) => {
        const numero = e.detail.numero;
        ui.showDetailPanel(numero);
    });
    
    // Resize de la fenêtre
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
        
        // Mettre à jour la carte
        await map.updateMetric(currentMetric, currentYear);
        
        // Mettre à jour les stats
        await ui.updateStatsPanel(currentMetric);
        
        hideLoading();
        
        log('✅ Carte rafraîchie', 'success');
        
    } catch (error) {
        hideLoading();
        log(`❌ Erreur rafraîchissement: ${error.message}`, 'error');
        alert(`Erreur lors du rafraîchissement:\n${error.message}`);
    }
}

/**
 * Gestion des erreurs globales
 */
window.addEventListener('error', (event) => {
    log(`❌ Erreur globale: ${event.error}`, 'error');
    console.error('Stack trace:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    log(`❌ Promise rejetée: ${event.reason}`, 'error');
    console.error('Raison:', event.reason);
});

/**
 * Démarrer l'application quand le DOM est prêt
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Logs de bienvenue
console.log('%c🏠 Dashboard Immobilier Paris', 'font-size: 20px; font-weight: bold; color: #667eea;');
console.log('%cVersion 1.0 - Prêt à l\'emploi', 'color: #22c55e;');
console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #667eea;');