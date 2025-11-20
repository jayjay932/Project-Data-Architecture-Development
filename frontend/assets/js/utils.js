/**
 * Fonctions utilitaires
 */

// Afficher/Cacher le loader
function showLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.classList.remove('hidden');
}

function hideLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.classList.add('hidden');
}

// Formatage des nombres
function formatNumber(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return Math.round(value).toLocaleString('fr-FR');
}

// Formatage des prix
function formatPrice(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return `${formatNumber(value)} €`;
}

// Formatage prix/m²
function formatPricePerM2(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return `${formatNumber(value)} €/m²`;
}

// Formatage des pourcentages
function formatPercent(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
}

// Obtenir la couleur pour une valeur
function getColorForValue(value, metric) {
    if (value === null || value === undefined || isNaN(value)) {
        return '#e0e0e0';
    }

    // Prix/m²
    if (metric.includes('prix_m2')) {
        if (value < 9000) return '#4ade80';
        if (value < 11000) return '#facc15';
        if (value < 13000) return '#fb923c';
        if (value < 14500) return '#f87171';
        return '#dc2626';
    }
    
    // Évolution
    if (metric.includes('evolution')) {
        if (value < -5) return '#dc2626';
        if (value < 0) return '#f87171';
        if (value < 5) return '#94a3b8';
        if (value < 10) return '#4ade80';
        return '#22c55e';
    }
    
    // Pollution (NO2, PM10, O3)
    if (metric.includes('no2') || metric.includes('pm10') || metric.includes('o3')) {
        if (value < 30) return '#22c55e';
        if (value < 50) return '#84cc16';
        if (value < 70) return '#facc15';
        if (value < 90) return '#fb923c';
        return '#dc2626';
    }
    
    // Transport (plus = mieux)
    if (metric.includes('stations') || metric.includes('lignes') || metric.includes('trafic')) {
        if (value < 3) return '#dbeafe';
        if (value < 6) return '#93c5fd';
        if (value < 10) return '#60a5fa';
        if (value < 15) return '#3b82f6';
        return '#1e40af';
    }
    
    // Pourcentages génériques
    if (metric.includes('pct')) {
        if (value < 10) return '#dbeafe';
        if (value < 20) return '#93c5fd';
        if (value < 30) return '#60a5fa';
        if (value < 40) return '#3b82f6';
        return '#1e40af';
    }
    
    // Défaut
    if (value < 20) return '#dbeafe';
    if (value < 40) return '#93c5fd';
    if (value < 60) return '#60a5fa';
    if (value < 80) return '#3b82f6';
    return '#1e40af';
}

// Créer une échelle de légende
function createLegendScale(values, metric) {
    const validValues = values.filter(v => v !== null && v !== undefined && !isNaN(v));
    if (validValues.length === 0) return [];
    
    const min = Math.min(...validValues);
    const max = Math.max(...validValues);
    const step = (max - min) / 4;
    
    const scale = [];
    for (let i = 0; i < 5; i++) {
        const value = min + (step * i);
        scale.push({
            value: value,
            color: getColorForValue(value, metric),
            label: formatValueForMetric(value, metric)
        });
    }
    
    return scale;
}

// Formater une valeur selon la métrique
function formatValueForMetric(value, metric) {
    if (metric.includes('prix_m2')) {
        return formatPricePerM2(value);
    } else if (metric.includes('prix')) {
        return formatPrice(value);
    } else if (metric.includes('evolution') || metric.includes('pct')) {
        return formatPercent(value);
    } else if (metric.includes('trafic')) {
        return formatNumber(value);
    } else {
        return formatNumber(value);
    }
}

// Obtenir le label d'une métrique
function getMetricLabel(metric) {
    const labels = {
        'prix_m2_median_2024': 'Prix/m² médian 2024',
        'prix_median_2024': 'Prix médian 2024',
        'evolution_prix_2020_2024_pct': 'Évolution prix 2020-2024',
        'tendance_prix_m2': 'Tendance du marché',
        'nb_appartements_2024': 'Nombre d\'appartements',
        'pct_T1_2024': 'Part de T1',
        'pct_T2_2024': 'Part de T2',
        'pct_T3_2024': 'Part de T3',
        'estimation_logement_social_pct': 'Logements sociaux',
        'nb_stations_metro': 'Stations de métro',
        'trafic_total_metro': 'Trafic métro total',
        'nb_lignes_metro': 'Lignes de métro',
        'no2_moyen': 'NO₂ moyen (µg/m³)',
        'pm10_moyen': 'PM10 moyen (µg/m³)',
        'o3_moyen': 'O₃ moyen (µg/m³)'
    };
    
    return labels[metric] || metric.replace(/_/g, ' ');
}

// Debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Log avec style
function log(message, type = 'info') {
    const styles = {
        info: 'color: #3b82f6; font-weight: bold;',
        success: 'color: #22c55e; font-weight: bold;',
        error: 'color: #dc2626; font-weight: bold;',
        warning: 'color: #f59e0b; font-weight: bold;'
    };
    console.log(`%c${message}`, styles[type] || styles.info);
}