/* =========================================================
   PATCH FINAL — Graphes panneau droit
   À charger APRÈS main.js
   ========================================================= */

(function () {
    'use strict';

    const API_BASE = 'http://localhost:5000/api';
    const YEARS = [2020, 2021, 2022, 2023, 2024, 2025];

    function hasValue(value) {
        return value !== null &&
            value !== undefined &&
            value !== '' &&
            value !== 'N/A' &&
            value !== 'nan' &&
            value !== 'NaN' &&
            !(typeof value === 'number' && Number.isNaN(value));
    }

    function toNumber(value) {
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

    function get(data, ...keys) {
        for (const key of keys) {
            if (data && Object.prototype.hasOwnProperty.call(data, key) && hasValue(data[key])) {
                return data[key];
            }
        }
        return null;
    }

    function formatNumber(value) {
        const n = toNumber(value);
        if (n === null) return '—';
        return Math.round(n).toLocaleString('fr-FR');
    }

    function formatCompact(value) {
        const n = toNumber(value);
        if (n === null) return '—';

        if (Math.abs(n) >= 1000000) {
            return `${(n / 1000000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })}M`;
        }

        if (Math.abs(n) >= 1000) {
            return `${(n / 1000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })}k`;
        }

        return formatNumber(n);
    }

    function formatDecimal(value, digits = 1) {
        const n = toNumber(value);
        if (n === null) return '—';

        return n.toLocaleString('fr-FR', {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits
        });
    }

    function formatPrice(value) {
        const n = toNumber(value);
        if (n === null) return '—';
        return `${formatNumber(n)} €`;
    }

    function formatPriceM2(value) {
        const n = toNumber(value);
        if (n === null) return '—';
        return `${formatNumber(n)} €/m²`;
    }

    function formatPercent(value, withSign = true) {
        const n = toNumber(value);
        if (n === null) return '—';

        const sign = withSign && n > 0 ? '+' : '';

        return `${sign}${n.toLocaleString('fr-FR', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        })}%`;
    }

    function escapeHtml(value) {
        if (!hasValue(value)) return '';

        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function unwrapApiResponse(json) {
        if (!json) return null;
        if (json.data && typeof json.data === 'object') return json.data;
        return json;
    }

    async function fetchArrondissement(numero) {
        const response = await fetch(`${API_BASE}/arrondissements/${numero}`);

        if (!response.ok) {
            throw new Error(`API ${response.status}`);
        }

        const json = await response.json();
        return unwrapApiResponse(json);
    }

    function injectStyles() {
        if (document.getElementById('detail-graphs-patch-style')) return;

        const style = document.createElement('style');
        style.id = 'detail-graphs-patch-style';
        style.textContent = `
            .udg-shell {
                display: flex;
                flex-direction: column;
                gap: 14px;
            }

            .udg-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--line, #e8ebf3);
            }

            .udg-header h2 {
                margin: 0;
                font-size: 23px;
                font-weight: 850;
                letter-spacing: -0.035em;
                color: #141a2a;
            }

            .udg-header p {
                margin: 6px 0 0;
                color: #667089;
                font-size: 13px;
                font-weight: 650;
                line-height: 1.45;
            }

            .udg-badge {
                min-width: 44px;
                height: 44px;
                display: grid;
                place-items: center;
                border-radius: 14px;
                color: white;
                font-weight: 900;
                background: linear-gradient(135deg, #557cf7, #a056f5);
                box-shadow: 0 12px 22px rgba(85, 124, 247, .24);
            }

            .udg-kpis {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .udg-kpi,
            .udg-section,
            .udg-chart-card {
                background: #ffffff;
                border: 1px solid var(--line, #e8ebf3);
                border-radius: 16px;
                box-shadow: 0 8px 22px rgba(20,30,55,.04);
            }

            .udg-kpi {
                padding: 15px;
            }

            .udg-kpi span {
                display: block;
                color: #667089;
                font-size: 12px;
                font-weight: 800;
                margin-bottom: 8px;
            }

            .udg-kpi strong {
                display: block;
                color: #141a2a;
                font-size: 20px;
                font-weight: 900;
                letter-spacing: -0.03em;
            }

            .udg-section {
                padding: 14px;
            }

            .udg-section-head {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 14px;
            }

            .udg-section-head h4 {
                margin: 0;
                color: #4f6df3;
                font-size: 15px;
                font-weight: 850;
            }

            .udg-section-head span {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 6px 10px;
                color: #5b45d8;
                background: #f2f0ff;
                font-size: 11px;
                font-weight: 850;
            }

            .udg-list {
                display: grid;
            }

            .udg-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                min-height: 42px;
                padding: 8px 0;
                border-bottom: 1px solid #eef1f6;
            }

            .udg-row:last-child {
                border-bottom: 0;
            }

            .udg-row span {
                color: #59647b;
                font-size: 13px;
                font-weight: 700;
            }

            .udg-row strong {
                text-align: right;
                color: #20283b;
                font-size: 13px;
                font-weight: 900;
            }

            .udg-positive {
                color: #17b26a !important;
            }

            .udg-negative {
                color: #ef4444 !important;
            }

            .udg-chart-stack {
                display: grid;
                gap: 14px;
            }

            .udg-chart-card {
                padding: 14px;
                background: #fbfcff;
            }

            .udg-chart-title {
                display: flex;
                flex-direction: column;
                gap: 3px;
                margin-bottom: 10px;
            }

            .udg-chart-title strong {
                color: #20283b;
                font-size: 14px;
                font-weight: 900;
            }

            .udg-chart-title small {
                color: #7c8598;
                font-size: 12px;
                font-weight: 650;
            }

            .udg-line {
                width: 100%;
                height: 165px;
                display: block;
                overflow: visible;
            }

            .udg-grid {
                stroke: #e8ebf3;
                stroke-width: 1;
            }

            .udg-line-path {
                fill: none;
                stroke: #557cf7;
                stroke-width: 3.4;
                stroke-linecap: round;
                stroke-linejoin: round;
            }

            .udg-dot {
                fill: #ffffff;
                stroke: #557cf7;
                stroke-width: 3;
            }

            .udg-x-label {
                fill: #667089;
                font-size: 11px;
                font-weight: 800;
            }

            .udg-minmax {
                display: flex;
                justify-content: space-between;
                margin-top: 4px;
                color: #7c8598;
                font-size: 11px;
                font-weight: 700;
            }

            .udg-bar-list {
                display: grid;
                gap: 12px;
            }

            .udg-bar-row {
                display: grid;
                gap: 7px;
            }

            .udg-bar-top {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                font-size: 13px;
            }

            .udg-bar-top span {
                color: #667089;
                font-weight: 750;
            }

            .udg-bar-top strong {
                color: #20283b;
                font-weight: 900;
            }

            .udg-bar-track {
                height: 10px;
                border-radius: 999px;
                background: #edf0f7;
                overflow: hidden;
            }

            .udg-bar-track i {
                display: block;
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, #557cf7, #a056f5);
            }

            .udg-div-list {
                display: grid;
                gap: 12px;
            }

            .udg-div-row {
                display: grid;
                grid-template-columns: 82px 1fr 68px;
                align-items: center;
                gap: 10px;
            }

            .udg-div-row span {
                color: #667089;
                font-size: 12px;
                font-weight: 750;
            }

            .udg-div-row strong {
                text-align: right;
                font-size: 12px;
                font-weight: 900;
            }

            .udg-div-track {
                position: relative;
                height: 10px;
                border-radius: 999px;
                background:
                    linear-gradient(
                        90deg,
                        transparent calc(50% - 1px),
                        #98a1b7 calc(50% - 1px),
                        #98a1b7 calc(50% + 1px),
                        transparent calc(50% + 1px)
                    ),
                    #edf0f7;
                overflow: hidden;
            }

            .udg-div-track i {
                position: absolute;
                top: 0;
                height: 100%;
                border-radius: inherit;
            }

            .udg-div-track i.pos {
                background: linear-gradient(90deg, #ffb45c, #ef4444);
            }

            .udg-div-track i.neg {
                background: linear-gradient(90deg, #17b26a, #8df0bd);
            }

            .udg-score-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .udg-score {
                padding: 14px;
                border-radius: 16px;
                background: #fbfcff;
                border: 1px solid var(--line, #e8ebf3);
            }

            .udg-score span {
                display: block;
                color: #59647b;
                font-size: 12px;
                font-weight: 850;
                margin-bottom: 8px;
            }

            .udg-score strong {
                display: block;
                font-size: 19px;
                font-weight: 900;
                color: #20283b;
                margin-bottom: 9px;
            }

            .udg-score-track {
                height: 8px;
                border-radius: 999px;
                background: #eef2f8;
                overflow: hidden;
            }

            .udg-score-track i {
                display: block;
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, #557cf7, #a056f5);
            }

            .udg-error {
                padding: 18px;
                border-radius: 16px;
                border: 1px solid #fee2e2;
                background: #fff7f7;
                color: #991b1b;
                font-weight: 750;
            }
        `;

        document.head.appendChild(style);
    }

    function lineChart(items, formatter) {
        const clean = items
            .map(item => ({
                label: String(item.label),
                value: toNumber(item.value)
            }))
            .filter(item => item.value !== null);

        if (clean.length < 2) return '';

        const values = clean.map(item => item.value);
        const width = 420;
        const height = 165;
        const padX = 34;
        const padY = 26;

        let min = Math.min(...values);
        let max = Math.max(...values);

        if (min === max) {
            min -= 1;
            max += 1;
        }

        const range = max - min;
        const step = (width - padX * 2) / Math.max(1, clean.length - 1);

        const points = clean.map((item, index) => {
            const x = padX + step * index;
            const y = height - padY - ((item.value - min) / range) * (height - padY * 2);
            return { ...item, x, y };
        });

        const uid = `udg-gradient-${Math.random().toString(36).slice(2)}`;

        const path = points
            .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
            .join(' ');

        const area = `${path} L ${points[points.length - 1].x.toFixed(1)} ${height - padY} L ${points[0].x.toFixed(1)} ${height - padY} Z`;

        return `
            <div>
                <svg class="udg-line" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="${uid}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#5d87ff" stop-opacity="0.24"></stop>
                            <stop offset="100%" stop-color="#5d87ff" stop-opacity="0"></stop>
                        </linearGradient>
                    </defs>

                    <line class="udg-grid" x1="${padX}" y1="${padY}" x2="${width - padX}" y2="${padY}"></line>
                    <line class="udg-grid" x1="${padX}" y1="${height / 2}" x2="${width - padX}" y2="${height / 2}"></line>
                    <line class="udg-grid" x1="${padX}" y1="${height - padY}" x2="${width - padX}" y2="${height - padY}"></line>

                    <path d="${area}" fill="url(#${uid})"></path>
                    <path class="udg-line-path" d="${path}"></path>

                    ${points.map(point => `
                        <circle class="udg-dot" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="4">
                            <title>${escapeHtml(point.label)} · ${escapeHtml(formatter(point.value))}</title>
                        </circle>
                    `).join('')}

                    ${points.map(point => `
                        <text class="udg-x-label" x="${point.x.toFixed(1)}" y="${height - 7}" text-anchor="middle">
                            ${escapeHtml(point.label)}
                        </text>
                    `).join('')}
                </svg>

                <div class="udg-minmax">
                    <span>Min ${escapeHtml(formatter(min))}</span>
                    <span>Max ${escapeHtml(formatter(max))}</span>
                </div>
            </div>
        `;
    }

    function bars(items, formatter, forcedMax = null) {
        const clean = items
            .map(item => ({
                ...item,
                value: toNumber(item.value)
            }))
            .filter(item => item.value !== null);

        if (!clean.length) return '';

        const max = forcedMax || Math.max(...clean.map(item => item.value)) || 1;

        return `
            <div class="udg-bar-list">
                ${clean.map(item => {
                    const width = Math.max(2, Math.min(100, (item.value / max) * 100));

                    return `
                        <div class="udg-bar-row">
                            <div class="udg-bar-top">
                                <span>${escapeHtml(item.label)}</span>
                                <strong>${escapeHtml(formatter(item))}</strong>
                            </div>
                            <div class="udg-bar-track">
                                <i style="width:${width}%"></i>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    function divergingBars(items) {
        const clean = items
            .map(item => ({
                label: item.label,
                value: toNumber(item.value)
            }))
            .filter(item => item.value !== null);

        if (!clean.length) return '';

        const maxAbs = Math.max(...clean.map(item => Math.abs(item.value))) || 1;

        return `
            <div class="udg-div-list">
                ${clean.map(item => {
                    const positive = item.value >= 0;
                    const width = Math.max(4, Math.min(50, Math.abs(item.value) / maxAbs * 50));

                    return `
                        <div class="udg-div-row">
                            <span>${escapeHtml(item.label)}</span>
                            <div class="udg-div-track">
                                <i class="${positive ? 'pos' : 'neg'}"
                                   style="${positive ? `left:50%;width:${width}%` : `right:50%;width:${width}%`}"></i>
                            </div>
                            <strong class="${positive ? 'udg-negative' : 'udg-positive'}">
                                ${formatPercent(item.value)}
                            </strong>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    function chartCard(title, subtitle, chartHtml) {
        if (!chartHtml) return '';

        return `
            <article class="udg-chart-card">
                <div class="udg-chart-title">
                    <strong>${escapeHtml(title)}</strong>
                    <small>${escapeHtml(subtitle)}</small>
                </div>
                ${chartHtml}
            </article>
        `;
    }

    function row(label, value, formatter, trend = false) {
        const n = toNumber(value);

        if (n === null) return '';

        let className = '';

        if (trend) {
            className = n <= 0 ? 'udg-positive' : 'udg-negative';
        }

        return `
            <div class="udg-row">
                <span>${escapeHtml(label)}</span>
                <strong class="${className}">${escapeHtml(formatter(value))}</strong>
            </div>
        `;
    }

    function textRow(label, value) {
        if (!hasValue(value)) return '';

        return `
            <div class="udg-row">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
            </div>
        `;
    }

    function section(title, badge, content) {
        if (!content) return '';

        return `
            <section class="udg-section">
                <div class="udg-section-head">
                    <h4>${escapeHtml(title)}</h4>
                    ${badge ? `<span>${escapeHtml(badge)}</span>` : ''}
                </div>
                ${content}
            </section>
        `;
    }

    function getYearSeries(data, prefix) {
        return YEARS
            .map(year => ({
                label: String(year),
                value: get(data, `${prefix}_${year}`)
            }))
            .filter(item => toNumber(item.value) !== null);
    }

    function getEvolutionSeries(data, prefix) {
        const periods = [
            ['2020-2021', `${prefix}_2020_2021_pct`],
            ['2021-2022', `${prefix}_2021_2022_pct`],
            ['2022-2023', `${prefix}_2022_2023_pct`],
            ['2023-2024', `${prefix}_2023_2024_pct`],
            ['2024-2025', `${prefix}_2024_2025_pct`]
        ];

        return periods
            .map(([label, key]) => ({
                label,
                value: get(data, key)
            }))
            .filter(item => toNumber(item.value) !== null);
    }

    function buildKpis(data) {
        const kpis = [
            {
                label: 'Prix/m² 2024',
                value: get(data, 'prix_m2_median_2024'),
                formatter: formatPriceM2
            },
            {
                label: 'Ventes 2024',
                value: get(data, 'nb_ventes_2024'),
                formatter: formatNumber
            },
            {
                label: 'Stations métro',
                value: get(data, 'nb_stations_metro'),
                formatter: formatNumber
            },
            {
                label: 'Attractivité',
                value: get(data, 'indice_attractivite'),
                formatter: v => `${formatDecimal(v, 1)}/10`
            }
        ].filter(item => toNumber(item.value) !== null);

        if (!kpis.length) return '';

        return `
            <div class="udg-kpis">
                ${kpis.map(item => `
                    <div class="udg-kpi">
                        <span>${escapeHtml(item.label)}</span>
                        <strong>${escapeHtml(item.formatter(item.value))}</strong>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function buildEvolutionSection(data) {
        const priceM2 = getYearSeries(data, 'prix_m2_median');
        const priceMedian = getYearSeries(data, 'prix_median');
        const sales = getYearSeries(data, 'nb_ventes');
        const evolPriceM2 = getEvolutionSeries(data, 'evolution_prix_m2');
        const evolSales = getEvolutionSeries(data, 'evolution_volume');

        const charts = [];

        if (priceM2.length >= 2) {
            charts.push(chartCard(
                'Évolution prix/m²',
                'Prix/m² médian — 2020 à 2025',
                lineChart(priceM2, formatPriceM2)
            ));
        }

        if (priceMedian.length >= 2) {
            charts.push(chartCard(
                'Évolution prix médian',
                'Transactions — 2020 à 2025',
                lineChart(priceMedian, formatPrice)
            ));
        }

        if (sales.length >= 2) {
            charts.push(chartCard(
                'Évolution volume de ventes',
                'Nombre de ventes — 2020 à 2025',
                lineChart(sales, formatNumber)
            ));
        }

        if (evolPriceM2.length >= 2) {
            charts.push(chartCard(
                'Variation annuelle prix/m²',
                'Pourcentage par période',
                divergingBars(evolPriceM2)
            ));
        }

        if (evolSales.length >= 2) {
            charts.push(chartCard(
                'Variation annuelle des ventes',
                'Pourcentage par période',
                divergingBars(evolSales)
            ));
        }

        if (!charts.length) return '';

        return section('📈 Graphes d’évolution', '2020–2025', `
            <div class="udg-chart-stack">
                ${charts.join('')}
            </div>
        `);
    }

    function buildMarketSection(data) {
        const content = [
            row('Prix/m² médian 2024', get(data, 'prix_m2_median_2024'), formatPriceM2),
            row('Prix médian 2024', get(data, 'prix_median_2024'), formatPrice),
            row('Nombre de ventes 2024', get(data, 'nb_ventes_2024'), formatNumber),
            row('Évolution prix 2020-2024', get(data, 'evolution_prix_2020_2024_pct'), v => formatPercent(v), true),
            row('Évolution prix/m² 2020-2024', get(data, 'evolution_prix_m2_2020_2024_pct'), v => formatPercent(v), true),
            row('Évolution prix/m² 2023-2024', get(data, 'evolution_prix_m2_2023_2024_pct'), v => formatPercent(v), true),
            row('Évolution annuelle moyenne', get(data, 'evolution_annuelle_moyenne_pct'), v => formatPercent(v), true),
            row('Volatilité prix/m²', get(data, 'volatilite_prix_m2'), v => formatDecimal(v, 1)),
            textRow('Tendance marché', get(data, 'tendance_prix_m2'))
        ].filter(Boolean).join('');

        return section('💰 Prix & marché', '2024', `<div class="udg-list">${content}</div>`);
    }

    function buildTypologySection(data) {
        const items = [
            { label: 'T1', value: get(data, 'pct_T1_2024'), count: get(data, 'nb_T1_2024') },
            { label: 'T2', value: get(data, 'pct_T2_2024'), count: get(data, 'nb_T2_2024') },
            { label: 'T3', value: get(data, 'pct_T3_2024'), count: get(data, 'nb_T3_2024') },
            { label: 'T4', value: get(data, 'pct_T4_2024'), count: get(data, 'nb_T4_2024') },
            { label: 'T5+', value: get(data, 'pct_T5plus_2024'), count: get(data, 'nb_T5plus_2024') }
        ].filter(item => toNumber(item.value) !== null);

        const chart = items.length
            ? chartCard(
                'Répartition T1 → T5+',
                'Part des ventes par typologie',
                bars(items, item => {
                    const count = toNumber(item.count);
                    return `${formatDecimal(item.value, 1)}%${count !== null ? ` · ${formatNumber(count)}` : ''}`;
                }, 100)
            )
            : '';

        const content = [
            chart,
            `<div class="udg-list">`,
            row('Appartements 2024', get(data, 'nb_appartements_2024', 'nb_appartement_2024'), formatNumber),
            row('Maisons 2024', get(data, 'nb_maisons_2024', 'nb_maison_2024'), formatNumber),
            row('Nombre de pièces moyen', get(data, 'nb_pieces_moyen'), v => formatDecimal(v, 1)),
            textRow('Type dominant 2024', get(data, 'type_dominant_2024')),
            `</div>`
        ].filter(Boolean).join('');

        return section('🏠 Typologie logements', '2024', content);
    }

    function buildTransportSection(data) {
        const items = [
            { label: 'Stations métro', value: get(data, 'nb_stations_metro') },
            { label: 'Lignes métro', value: get(data, 'nb_lignes_metro') },
            { label: 'Lignes RER', value: get(data, 'nb_lignes_rer') }
        ].filter(item => toNumber(item.value) !== null);

        const chart = items.length
            ? chartCard(
                'Offre de transport',
                'Métro et RER',
                bars(items, item => formatNumber(item.value))
            )
            : '';

        const content = [
            chart,
            `<div class="udg-list">`,
            row('Trafic métro annuel', get(data, 'trafic_total_metro'), formatNumber),
            textRow('Lignes métro', get(data, 'lignes_metro')),
            textRow('Lignes RER', get(data, 'lignes_rer')),
            `</div>`
        ].filter(Boolean).join('');

        return section('🚇 Transport', 'Réseau ferré', content);
    }

    function buildAirSection(data) {
        const items = [
            { label: 'NO₂', value: get(data, 'no2_moyen') },
            { label: 'PM10', value: get(data, 'pm10_moyen') },
            { label: 'O₃', value: get(data, 'o3_moyen') }
        ].filter(item => toNumber(item.value) !== null);

        const chart = items.length
            ? chartCard(
                'Polluants moyens',
                'Concentration en µg/m³',
                bars(items, item => `${formatDecimal(item.value, 1)} µg/m³`)
            )
            : '';

        const content = [
            chart,
            `<div class="udg-list">`,
            textRow('Qualité dominante', get(data, 'qualite_air_dominante')),
            `</div>`
        ].filter(Boolean).join('');

        return section('🌫️ Qualité de l’air', 'µg/m³', content);
    }

    function buildDemoSection(data) {
        const content = [
            row('Population 2022', get(data, 'population_2022'), formatNumber),
            row('Ménages 2022', get(data, 'nb_menages_2022'), formatNumber),
            row('Logements 2022', get(data, 'nb_logements_2022'), formatNumber),
            row('Superficie', get(data, 'superficie_km2'), v => `${formatDecimal(v, 2)} km²`),
            row('Densité', get(data, 'densite_pop_km2'), v => `${formatNumber(v)} hab/km²`),
            row('Revenu médian', get(data, 'revenu_median'), formatPrice)
        ].filter(Boolean).join('');

        return section('👥 Démographie & revenus', 'INSEE', `<div class="udg-list">${content}</div>`);
    }

    function buildSocialSection(data) {
        const content = [
            row('Logements sociaux', get(data, 'nb_logements_sociaux_apur'), formatNumber),
            row('Part logements sociaux', get(data, 'part_logements_sociaux_apur_pct'), v => formatPercent(v, false)),
            textRow('Estimation', get(data, 'estimation_logement_social_pct')),
            row('Effort achat', get(data, 'ratio_effort_achat'), v => `${formatDecimal(v, 1)} ans`)
        ].filter(Boolean).join('');

        return section('🏢 Social & accessibilité', 'APUR', `<div class="udg-list">${content}</div>`);
    }

    function buildScoresSection(data) {
        const scores = [
            { label: 'Accessibilité', value: get(data, 'indice_accessibilite') },
            { label: 'Tension sociale', value: get(data, 'indice_tension_sociale') },
            { label: 'Attractivité', value: get(data, 'indice_attractivite') },
            { label: 'Pression immo', value: get(data, 'indice_pression_immo') }
        ].filter(item => toNumber(item.value) !== null);

        if (!scores.length) return '';

        const html = `
            <div class="udg-score-grid">
                ${scores.map(score => {
                    const value = toNumber(score.value);
                    const width = Math.max(0, Math.min(100, value * 10));

                    return `
                        <div class="udg-score">
                            <span>${escapeHtml(score.label)}</span>
                            <strong>${formatDecimal(value, 1)}/10</strong>
                            <div class="udg-score-track">
                                <i style="width:${width}%"></i>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        return section('📊 Indices composites', '0 à 10', html);
    }

    function buildDetail(numero, data) {
        const arr = get(data, 'arrondissement', 'Arrondissement') || numero;

        return `
            <div class="udg-shell">
                <div class="udg-header">
                    <div>
                        <h2>${escapeHtml(arr)}e arrondissement</h2>
                        <p>Analyse complète : prix, évolutions, typologie, transport, pollution, démographie et scores.</p>
                    </div>
                    <div class="udg-badge">${escapeHtml(arr)}</div>
                </div>

                ${buildKpis(data)}
                ${buildMarketSection(data)}
                ${buildEvolutionSection(data)}
                ${buildTypologySection(data)}
                ${buildTransportSection(data)}
                ${buildAirSection(data)}
                ${buildDemoSection(data)}
                ${buildSocialSection(data)}
                ${buildScoresSection(data)}
            </div>
        `;
    }

    async function renderArrondissement(numero) {
        injectStyles();

        const detailContent = document.getElementById('detail-content');
        const detailPanel = document.getElementById('detail-panel');

        if (!detailContent) return;

        if (detailPanel) {
            detailPanel.classList.remove('hidden');
        }

        detailContent.innerHTML = `
            <div class="udg-section">
                <div class="udg-section-head">
                    <h4>Chargement arrondissement ${escapeHtml(numero)}</h4>
                    <span>API</span>
                </div>
                <p style="color:#667089;font-weight:700;">Récupération des vraies données...</p>
            </div>
        `;

        try {
            const data = await fetchArrondissement(numero);

            if (!data || typeof data !== 'object') {
                throw new Error('Réponse API vide');
            }

            detailContent.innerHTML = buildDetail(numero, data);
        } catch (error) {
            detailContent.innerHTML = `
                <div class="udg-error">
                    Impossible d’afficher les graphes pour l’arrondissement ${escapeHtml(numero)}.<br>
                    ${escapeHtml(error.message)}
                </div>
            `;
        }
    }

    function patchExistingUI() {
        try {
            if (typeof UI !== 'undefined' && UI.prototype) {
                UI.prototype.showDetailPanel = function (numero) {
                    return renderArrondissement(numero);
                };
            }
        } catch (error) {
            console.warn('Patch UI non appliqué:', error);
        }
    }

    patchExistingUI();

    window.addEventListener('arrondissement-selected', function (event) {
        const numero = event.detail && event.detail.numero;
        if (numero) renderArrondissement(numero);
    });

    window.showArrondissementGraphs = renderArrondissement;

    document.addEventListener('DOMContentLoaded', function () {
        patchExistingUI();

        setTimeout(function () {
            const detailContent = document.getElementById('detail-content');

            if (
                detailContent &&
                detailContent.textContent &&
                detailContent.textContent.includes('Sélectionnez')
            ) {
                renderArrondissement(12);
            }
        }, 800);
    });

    setTimeout(patchExistingUI, 1200);
})();