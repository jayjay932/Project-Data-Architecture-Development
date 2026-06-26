/**
 * Fonctions utilitaires — Dashboard Immobilier Paris
 * Version corrigée : pas de "N/A", formatage propre, métriques par année.
 */

// -----------------------------------------------------------------------------
// Loader
// -----------------------------------------------------------------------------

function showLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.classList.remove('hidden');
}

function hideLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.classList.add('hidden');
}

// -----------------------------------------------------------------------------
// Valeurs
// -----------------------------------------------------------------------------

function hasValue(value) {
    return value !== null &&
        value !== undefined &&
        value !== '' &&
        value !== 'N/A' &&
        value !== 'nan' &&
        value !== 'NaN' &&
        !(typeof value === 'number' && Number.isNaN(value));
}

function asNumber(value) {
    if (!hasValue(value)) return null;

    if (typeof value === 'number') {
        return Number.isFinite(value) ? value : null;
    }

    const cleaned = String(value)
        .replace(/\s/g, '')
        .replace(',', '.')
        .replace('%', '')
        .replace('€', '');

    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
}

function safeText(value) {
    return hasValue(value) ? String(value) : '';
}

// -----------------------------------------------------------------------------
// Formatage
// -----------------------------------------------------------------------------

function formatNumber(value) {
    const n = asNumber(value);
    if (n === null) return '—';
    return Math.round(n).toLocaleString('fr-FR');
}

function formatCompact(value) {
    const n = asNumber(value);
    if (n === null) return '—';

    if (Math.abs(n) >= 1_000_000) {
        return `${(n / 1_000_000).toLocaleString('fr-FR', {
            maximumFractionDigits: 1
        })}M`;
    }

    if (Math.abs(n) >= 1_000) {
        return `${(n / 1_000).toLocaleString('fr-FR', {
            maximumFractionDigits: 1
        })}k`;
    }

    return formatNumber(n);
}

function formatDecimal(value, digits = 1) {
    const n = asNumber(value);
    if (n === null) return '—';

    return n.toLocaleString('fr-FR', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    });
}

function formatPrice(value) {
    const n = asNumber(value);
    if (n === null) return '—';
    return `${formatNumber(n)} €`;
}

function formatPricePerM2(value) {
    const n = asNumber(value);
    if (n === null) return '—';
    return `${formatNumber(n)} €/m²`;
}

function formatPercent(value) {
    const n = asNumber(value);
    if (n === null) return '—';
    const sign = n > 0 ? '+' : '';
    return `${sign}${n.toLocaleString('fr-FR', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    })}%`;
}

function formatValueForMetric(value, metric) {
    const n = asNumber(value);
    if (n === null) return '—';

    if (metric.includes('prix_m2')) return formatPricePerM2(n);
    if (metric.includes('prix_median')) return formatPrice(n);
    if (metric.includes('prix') && !metric.includes('evolution')) return formatPrice(n);
    if (metric.includes('evolution') || metric.includes('pct') || metric.includes('part_')) return formatPercent(n);
    if (metric.includes('trafic')) return formatCompact(n);
    if (metric.includes('indice')) return `${formatDecimal(n, 1)}/10`;
    if (metric.includes('ratio_effort')) return `${formatDecimal(n, 1)} ans`;
    if (metric.includes('densite')) return `${formatNumber(n)} hab/km²`;
    if (metric.includes('revenu')) return formatPrice(n);
    if (metric.includes('no2') || metric.includes('pm10') || metric.includes('o3')) return `${formatDecimal(n, 1)} µg/m³`;

    return formatNumber(n);
}

// -----------------------------------------------------------------------------
// Métriques par année
// -----------------------------------------------------------------------------

function getYearAwareMetric(metric, year) {
    if (!metric || !year) return metric;

    const y = String(year);

    return metric
        .replace(/prix_m2_median_\d{4}/, `prix_m2_median_${y}`)
        .replace(/prix_median_\d{4}/, `prix_median_${y}`)
        .replace(/nb_ventes_\d{4}/, `nb_ventes_${y}`)
        .replace(/nb_appartement_\d{4}/, `nb_appartement_${y}`)
        .replace(/nb_appartements_\d{4}/, `nb_appartements_${y}`)
        .replace(/pct_appartement_\d{4}/, `pct_appartement_${y}`)
        .replace(/nb_T1_\d{4}/, `nb_T1_${y}`)
        .replace(/pct_T1_\d{4}/, `pct_T1_${y}`)
        .replace(/nb_T2_\d{4}/, `nb_T2_${y}`)
        .replace(/pct_T2_\d{4}/, `pct_T2_${y}`)
        .replace(/nb_T3_\d{4}/, `nb_T3_${y}`)
        .replace(/pct_T3_\d{4}/, `pct_T3_${y}`)
        .replace(/nb_T4_\d{4}/, `nb_T4_${y}`)
        .replace(/pct_T4_\d{4}/, `pct_T4_${y}`)
        .replace(/nb_T5plus_\d{4}/, `nb_T5plus_${y}`)
        .replace(/pct_T5plus_\d{4}/, `pct_T5plus_${y}`);
}

// -----------------------------------------------------------------------------
// Couleurs carte
// -----------------------------------------------------------------------------

function getColorForValue(value, metric) {
    const n = asNumber(value);

    if (n === null) {
        return '#d8dee9';
    }

    if (metric.includes('prix_m2')) {
        if (n < 9000) return '#d8f3dc';
        if (n < 10500) return '#b7e4c7';
        if (n < 12000) return '#f9c74f';
        if (n < 13500) return '#f9844a';
        return '#c1121f';
    }

    if (metric.includes('prix') && !metric.includes('evolution')) {
        if (n < 400000) return '#d8f3dc';
        if (n < 550000) return '#b7e4c7';
        if (n < 750000) return '#f9c74f';
        if (n < 1000000) return '#f9844a';
        return '#c1121f';
    }

    if (metric.includes('evolution')) {
        if (n <= -10) return '#1b9e77';
        if (n < -3) return '#52b788';
        if (n <= 3) return '#adb5bd';
        if (n <= 10) return '#f9844a';
        return '#c1121f';
    }

    if (metric.includes('no2') || metric.includes('pm10') || metric.includes('o3')) {
        if (n < 30) return '#2d6a4f';
        if (n < 35) return '#52b788';
        if (n < 40) return '#f9c74f';
        if (n < 45) return '#f9844a';
        return '#c1121f';
    }

    if (metric.includes('stations') || metric.includes('lignes') || metric.includes('trafic')) {
        if (n < 4) return '#dbeafe';
        if (n < 8) return '#93c5fd';
        if (n < 12) return '#60a5fa';
        if (n < 16) return '#2563eb';
        return '#1e3a8a';
    }

    if (metric.includes('logements_sociaux') || metric.includes('part_logements')) {
        if (n < 10) return '#fee2e2';
        if (n < 20) return '#fed7aa';
        if (n < 30) return '#fde68a';
        if (n < 40) return '#bbf7d0';
        return '#22c55e';
    }

    if (metric.includes('indice')) {
        if (n < 2) return '#fee2e2';
        if (n < 4) return '#fed7aa';
        if (n < 6) return '#fde68a';
        if (n < 8) return '#93c5fd';
        return '#2563eb';
    }

    if (metric.includes('pct')) {
        if (n < 10) return '#eff6ff';
        if (n < 20) return '#bfdbfe';
        if (n < 30) return '#93c5fd';
        if (n < 40) return '#3b82f6';
        return '#1d4ed8';
    }

    if (n < 20) return '#eff6ff';
    if (n < 40) return '#bfdbfe';
    if (n < 60) return '#93c5fd';
    if (n < 80) return '#3b82f6';
    return '#1d4ed8';
}

function createLegendScale(values, metric) {
    const validValues = values
        .map(asNumber)
        .filter(v => v !== null);

    if (!validValues.length) return [];

    const min = Math.min(...validValues);
    const max = Math.max(...validValues);

    if (min === max) {
        return [{
            value: min,
            color: getColorForValue(min, metric),
            label: formatValueForMetric(min, metric)
        }];
    }

    const scale = [];
    const steps = 5;

    for (let i = 0; i < steps; i++) {
        const value = min + ((max - min) / (steps - 1)) * i;
        scale.push({
            value,
            color: getColorForValue(value, metric),
            label: formatValueForMetric(value, metric)
        });
    }

    return scale;
}

// -----------------------------------------------------------------------------
// Labels
// -----------------------------------------------------------------------------

function getMetricLabel(metric) {
    const labels = {
        prix_m2_median_2020: 'Prix/m² médian 2020',
        prix_m2_median_2021: 'Prix/m² médian 2021',
        prix_m2_median_2022: 'Prix/m² médian 2022',
        prix_m2_median_2023: 'Prix/m² médian 2023',
        prix_m2_median_2024: 'Prix/m² médian 2024',
        prix_m2_median_2025: 'Prix/m² médian 2025',

        prix_median_2024: 'Prix médian 2024',
        nb_ventes_2024: 'Nombre de ventes 2024',

        nb_appartements_2024: 'Nombre d’appartements 2024',
        nb_maisons_2024: 'Nombre de maisons 2024',
        pct_T1_2024: 'Part de T1',
        pct_T2_2024: 'Part de T2',
        pct_T3_2024: 'Part de T3',
        pct_T4_2024: 'Part de T4',
        pct_T5plus_2024: 'Part de T5+',

        nb_logements_sociaux_apur: 'Logements sociaux',
        part_logements_sociaux_apur_pct: 'Part logements sociaux',

        nb_stations_metro: 'Stations métro',
        trafic_total_metro: 'Trafic métro total',
        nb_lignes_metro: 'Lignes métro',
        nb_lignes_rer: 'Lignes RER',

        no2_moyen: 'NO₂ moyen',
        pm10_moyen: 'PM10 moyen',
        o3_moyen: 'O₃ moyen',

        population_2022: 'Population 2022',
        densite_pop_km2: 'Densité population',
        revenu_median: 'Revenu médian',

        indice_accessibilite: 'Indice d’accessibilité',
        indice_tension_sociale: 'Indice de tension sociale',
        indice_attractivite: 'Indice d’attractivité',
        indice_pression_immo: 'Indice de pression immobilière',
        ratio_effort_achat: 'Effort d’achat'
    };

    return labels[metric] || metric.replace(/_/g, ' ');
}

function getIndicatorDescription(metric) {
    const descriptions = {
        prix_m2_median_2024: {
            text: 'Prix médian au mètre carré par arrondissement.',
            source: 'DVF — agrégation arrondissement'
        },
        prix_median_2024: {
            text: 'Prix médian des ventes immobilières.',
            source: 'DVF — ventes filtrées'
        },
        nb_ventes_2024: {
            text: 'Volume de mutations immobilières.',
            source: 'DVF'
        },
        nb_stations_metro: {
            text: 'Nombre de stations de métro dans l’arrondissement.',
            source: 'Données transport'
        },
        trafic_total_metro: {
            text: 'Trafic annuel entrant cumulé des stations métro.',
            source: 'RATP / réseau ferré'
        },
        no2_moyen: {
            text: 'Concentration moyenne en dioxyde d’azote.',
            source: 'Qualité de l’air'
        },
        pm10_moyen: {
            text: 'Concentration moyenne en particules PM10.',
            source: 'Qualité de l’air'
        },
        o3_moyen: {
            text: 'Concentration moyenne en ozone.',
            source: 'Qualité de l’air'
        }
    };

    return descriptions[metric] || {
        text: getMetricLabel(metric),
        source: 'Données agrégées'
    };
}

// -----------------------------------------------------------------------------
// Outils divers
// -----------------------------------------------------------------------------

function debounce(func, wait) {
    let timeout;

    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

function log(message, type = 'info') {
    const styles = {
        info: 'color:#2563eb;font-weight:700;',
        success: 'color:#16a34a;font-weight:700;',
        error: 'color:#dc2626;font-weight:700;',
        warning: 'color:#f59e0b;font-weight:700;'
    };

    console.log(`%c${message}`, styles[type] || styles.info);
}
/* =========================================================
   FIX GLOBAL — Parser numéro arrondissement
   Corrige : parseArrondissementNumber is not defined
   ========================================================= */

function parseArrondissementNumber(input) {
    if (input === null || input === undefined) return null;

    // Si on reçoit directement un nombre
    if (typeof input === 'number') {
        if (Number.isFinite(input)) {
            if (input >= 1 && input <= 20) return input;

            // Cas code INSEE type 75112 / 75012
            const lastTwo = input % 100;
            if (lastTwo >= 1 && lastTwo <= 20) return lastTwo;
        }

        return null;
    }

    // Si on reçoit un objet GeoJSON ou un objet API
    if (typeof input === 'object') {
        const source = input.properties || input;

        const possibleKeys = [
            'numero',
            'arrondissement',
            'arrondissement_numero',
            'num_arrondissement',
            'c_ar',
            'c_arinsee',
            'l_ar',
            'nom',
            'name'
        ];

        for (const key of possibleKeys) {
            if (source[key] !== undefined && source[key] !== null) {
                const parsed = parseArrondissementNumber(source[key]);
                if (parsed !== null) return parsed;
            }
        }

        return null;
    }

    // Si on reçoit une string : "12", "12e", "Paris 12", "75012", etc.
    const text = String(input).trim();

    if (!text) return null;

    // Cas code INSEE Paris type 75112 ou 75012
    const inseeMatch = text.match(/75[01](\d{2})/);
    if (inseeMatch) {
        const n = parseInt(inseeMatch[1], 10);
        if (n >= 1 && n <= 20) return n;
    }

    // Cas standard : "12e", "12 arrondissement", "Paris 12"
    const normalMatch = text.match(/\b([1-9]|1[0-9]|20)\b/);
    if (normalMatch) {
        const n = parseInt(normalMatch[1], 10);
        if (n >= 1 && n <= 20) return n;
    }

    return null;
}

// Exposition globale pour tous les fichiers JS
window.parseArrondissementNumber = parseArrondissementNumber;