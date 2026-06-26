/**
 * Gestion de l'interface utilisateur
 * Version propre : panneau droit + graphes + T1/T2/T3/T4/T5 compatibles majuscules/minuscules.
 */

class UI {
    constructor(api) {
        this.api = api;
        this.currentArrondissement = null;
    }

    unwrapApiResponse(response) {
        if (!response) return null;
        if (response.data && typeof response.data === 'object') return response.data;
        return response;
    }

    getValue(data, ...keys) {
        for (const key of keys) {
            if (
                data &&
                Object.prototype.hasOwnProperty.call(data, key) &&
                hasValue(data[key])
            ) {
                return data[key];
            }
        }

        return null;
    }

    async showDetailPanel(numero) {
        try {
            this.currentArrondissement = numero;
            showLoading();

            const response = await this.api.getArrondissement(numero);
            const data = this.unwrapApiResponse(response);

            hideLoading();

            if (!data) {
                this.showError('Données non disponibles');
                return;
            }

            const detailContent = document.getElementById('detail-content');
            const detailPanel = document.getElementById('detail-panel');

            if (detailContent) {
                detailContent.innerHTML = this.buildDetailContent(numero, data);
            }

            if (detailPanel) {
                detailPanel.classList.remove('hidden');
            }
        } catch (error) {
            hideLoading();
            log(`❌ Erreur affichage détails: ${error.message}`, 'error');
            this.showError('Erreur de chargement');
        }
    }

    buildDetailContent(numero, data) {
        return `
            <div class="detail-top">
                <div>
                    <div class="detail-title-wrap">
                        <h2>${numero}e arrondissement</h2>
                        ${data.tendance_prix_m2 ? `<span class="status-pill">${safeText(data.tendance_prix_m2)}</span>` : ''}
                    </div>
                    <p class="detail-subtitle">
                        Analyse complète : prix, évolutions, typologie, transport, pollution, démographie et scores.
                    </p>
                </div>
                <button class="star-btn" type="button">★</button>
            </div>

            <div class="tabs">
                <div class="tab active">Synthèse</div>
                <div class="tab">Graphes</div>
                <div class="tab">Indices</div>
            </div>

            ${this.buildKpiCards(data)}
            ${this.buildPrixSection(data)}
            ${this.buildEvolutionGraphs(data)}
            ${this.buildMoyennesGraph(data)}
            ${this.buildTypologieGraph(data)}
            ${this.buildTransportGraph(data)}
            ${this.buildPollutionGraph(data)}
            ${this.buildLogementSocialGraph(data)}
            ${this.buildDemographieSection(data)}
            ${this.buildIndicateursSection(data)}
        `;
    }

    buildKpiCards(data) {
        const items = [
            {
                label: 'Prix/m² 2024',
                value: data.prix_m2_median_2024,
                formatter: formatPricePerM2,
                icon: '€/m²'
            },
            {
                label: 'Ventes 2024',
                value: data.nb_ventes_2024,
                formatter: formatNumber,
                icon: '🏷️'
            },
            {
                label: 'Stations métro',
                value: data.nb_stations_metro,
                formatter: formatNumber,
                icon: '🚇'
            },
            {
                label: 'Attractivité',
                value: data.indice_attractivite,
                formatter: v => `${formatDecimal(v, 1)}/10`,
                icon: '⭐'
            }
        ].filter(item => asNumber(item.value) !== null);

        if (!items.length) return '';

        return `
            <div class="right-kpi-grid">
                ${items.map(item => `
                    <div class="right-kpi-card">
                        <span>${item.icon}</span>
                        <strong>${item.formatter(item.value)}</strong>
                        <small>${item.label}</small>
                    </div>
                `).join('')}
            </div>
        `;
    }

    buildPrixSection(data) {
        const rows = [
            this.buildDetailRow('Prix/m² médian 2024', data.prix_m2_median_2024, formatPricePerM2),
            this.buildDetailRow('Prix médian 2024', data.prix_median_2024, formatPrice),
            this.buildDetailRow('Nombre de ventes 2024', data.nb_ventes_2024, formatNumber),
            this.buildDetailRow('Évolution prix 2020-2024', data.evolution_prix_2020_2024_pct, formatPercent, true),
            this.buildDetailRow('Évolution prix/m² 2020-2024', data.evolution_prix_m2_2020_2024_pct, formatPercent, true),
            this.buildDetailRow('Évolution prix/m² 2023-2024', data.evolution_prix_m2_2023_2024_pct, formatPercent, true),
            this.buildTextRow('Tendance marché', data.tendance_prix_m2),
            this.buildDetailRow('Volatilité prix/m²', data.volatilite_prix_m2, v => formatDecimal(v, 1))
        ].filter(Boolean).join('');

        if (!rows) return '';

        return `
            <section class="detail-section">
                <h4>💰 Prix & marché</h4>
                <div class="metric-list">${rows}</div>
            </section>
        `;
    }

    buildEvolutionGraphs(data) {
        const priceM2 = this.getYearSeries(data, 'prix_m2_median');
        const priceMedian = this.getYearSeries(data, 'prix_median');
        const ventes = this.getYearSeries(data, 'nb_ventes');
        const evolPrixM2 = this.getEvolutionSeries(data, 'evolution_prix_m2');
        const evolVolume = this.getEvolutionSeries(data, 'evolution_volume');

        const blocks = [];

        if (priceM2.length >= 2) {
            blocks.push(this.chartCard(
                'Évolution prix/m²',
                'Prix/m² médian par année',
                this.lineChart(priceM2, formatPricePerM2)
            ));
        }

        if (priceMedian.length >= 2) {
            blocks.push(this.chartCard(
                'Évolution prix médian',
                'Prix médian des transactions',
                this.lineChart(priceMedian, formatPrice)
            ));
        }

        if (ventes.length >= 2) {
            blocks.push(this.chartCard(
                'Évolution ventes',
                'Volume annuel de ventes',
                this.lineChart(ventes, formatNumber)
            ));
        }

        if (evolPrixM2.length >= 2) {
            blocks.push(this.chartCard(
                'Variation annuelle prix/m²',
                'Pourcentage par période',
                this.divergingBars(evolPrixM2)
            ));
        }

        if (evolVolume.length >= 2) {
            blocks.push(this.chartCard(
                'Variation volume de ventes',
                'Pourcentage par période',
                this.divergingBars(evolVolume)
            ));
        }

        if (!blocks.length) return '';

        return `
            <section class="detail-section chart-section">
                <div class="section-head">
                    <h4>📈 Graphes d’évolution</h4>
                    <span>2020–2025</span>
                </div>
                <div class="chart-stack">
                    ${blocks.join('')}
                </div>
            </section>
        `;
    }

    buildMoyennesGraph(data) {
        const items = [
            {
                label: 'Évol. annuelle moy.',
                value: data.evolution_annuelle_moyenne_pct,
                formatter: formatPercent
            },
            {
                label: 'Volatilité prix/m²',
                value: data.volatilite_prix_m2,
                formatter: v => formatDecimal(v, 1)
            },
            {
                label: 'Pièces moyennes',
                value: data.nb_pieces_moyen,
                formatter: v => formatDecimal(v, 1)
            },
            {
                label: 'Effort achat',
                value: data.ratio_effort_achat,
                formatter: v => `${formatDecimal(v, 1)} ans`
            }
        ].filter(item => asNumber(item.value) !== null);

        if (!items.length) return '';

        return `
            <section class="detail-section chart-section">
                <h4>📌 Moyennes & ratios</h4>
                <div class="mini-kpi-strip">
                    ${items.map(item => `
                        <div>
                            <span>${item.label}</span>
                            <strong>${item.formatter(item.value)}</strong>
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }

    buildTypologieGraph(data) {
        const typologies = [
            {
                label: 'T1',
                value: this.getValue(data, 'pct_T1_2024', 'pct_t1_2024'),
                count: this.getValue(data, 'nb_T1_2024', 'nb_t1_2024')
            },
            {
                label: 'T2',
                value: this.getValue(data, 'pct_T2_2024', 'pct_t2_2024'),
                count: this.getValue(data, 'nb_T2_2024', 'nb_t2_2024')
            },
            {
                label: 'T3',
                value: this.getValue(data, 'pct_T3_2024', 'pct_t3_2024'),
                count: this.getValue(data, 'nb_T3_2024', 'nb_t3_2024')
            },
            {
                label: 'T4',
                value: this.getValue(data, 'pct_T4_2024', 'pct_t4_2024'),
                count: this.getValue(data, 'nb_T4_2024', 'nb_t4_2024')
            },
            {
                label: 'T5+',
                value: this.getValue(data, 'pct_T5plus_2024', 'pct_t5plus_2024'),
                count: this.getValue(data, 'nb_T5plus_2024', 'nb_t5plus_2024')
            }
        ].filter(item => asNumber(item.value) !== null);

        const types = [
            {
                label: 'Appartements',
                value: this.getValue(data, 'pct_appartements', 'pct_appartement_2024', 'pct_appartements_2024')
            },
            {
                label: 'Maisons',
                value: this.getValue(data, 'pct_maisons', 'pct_maison_2024', 'pct_maisons_2024')
            },
            {
                label: 'Dépendances',
                value: this.getValue(data, 'pct_dépendance_2024', 'pct_dependance_2024')
            },
            {
                label: 'Locaux',
                value: this.getValue(data, 'pct_local_industriel._commercial_ou_assimilé_2024', 'pct_local_industriel_commercial_ou_assimile_2024')
            }
        ].filter(item => asNumber(item.value) !== null && asNumber(item.value) > 0);

        const rows = [
            this.buildDetailRow('Appartements 2024', this.getValue(data, 'nb_appartements_2024', 'nb_appartement_2024'), formatNumber),
            this.buildDetailRow('Maisons 2024', this.getValue(data, 'nb_maisons_2024', 'nb_maison_2024'), formatNumber),
            this.buildDetailRow('Nombre pièces moyen', data.nb_pieces_moyen, v => formatDecimal(v, 1)),
            this.buildTextRow('Type dominant 2024', data.type_dominant_2024)
        ].filter(Boolean).join('');

        if (!typologies.length && !types.length && !rows) return '';

        return `
            <section class="detail-section chart-section">
                <div class="section-head">
                    <h4>🏠 Typologie logements</h4>
                    <span>2024</span>
                </div>

                ${typologies.length ? `
                    <div class="chart-card">
                        <div class="chart-card-head">
                            <strong>Répartition T1 → T5+</strong>
                            <small>Part des ventes par typologie</small>
                        </div>
                        ${this.horizontalBars(typologies, item => {
                            const count = asNumber(item.count);
                            return `${formatDecimal(item.value, 1)}%${count !== null ? ` · ${formatNumber(count)}` : ''}`;
                        }, 100)}
                    </div>
                ` : ''}

                ${types.length ? `
                    <div class="chart-card">
                        <div class="chart-card-head">
                            <strong>Types de biens</strong>
                            <small>Répartition par catégorie</small>
                        </div>
                        ${this.horizontalBars(types, item => `${formatDecimal(item.value, 1)}%`, 100)}
                    </div>
                ` : ''}

                ${rows ? `<div class="metric-list">${rows}</div>` : ''}
            </section>
        `;
    }

    buildTransportGraph(data) {
        const items = [
            { label: 'Stations métro', value: data.nb_stations_metro },
            { label: 'Lignes métro', value: data.nb_lignes_metro },
            { label: 'Lignes RER', value: data.nb_lignes_rer }
        ].filter(item => asNumber(item.value) !== null);

        if (!items.length && asNumber(data.trafic_total_metro) === null && !data.lignes_metro && !data.lignes_rer) {
            return '';
        }

        return `
            <section class="detail-section chart-section">
                <div class="section-head">
                    <h4>🚇 Transport</h4>
                    <span>Réseau ferré</span>
                </div>

                ${items.length ? `
                    <div class="chart-card">
                        ${this.horizontalBars(items, item => formatNumber(item.value))}
                    </div>
                ` : ''}

                <div class="metric-list">
                    ${this.buildDetailRow('Trafic métro annuel', data.trafic_total_metro, formatNumber)}
                    ${this.buildTextRow('Lignes métro', data.lignes_metro)}
                    ${this.buildTextRow('Lignes RER', data.lignes_rer)}
                </div>
            </section>
        `;
    }

    buildPollutionGraph(data) {
        const items = [
            { label: 'NO₂', value: data.no2_moyen },
            { label: 'PM10', value: data.pm10_moyen },
            { label: 'O₃', value: data.o3_moyen }
        ].filter(item => asNumber(item.value) !== null);

        if (!items.length && !data.qualite_air_dominante) return '';

        return `
            <section class="detail-section chart-section">
                <div class="section-head">
                    <h4>🌫️ Qualité de l’air</h4>
                    <span>µg/m³</span>
                </div>

                ${items.length ? `
                    <div class="chart-card">
                        ${this.horizontalBars(items, item => `${formatDecimal(item.value, 1)} µg/m³`)}
                    </div>
                ` : ''}

                <div class="metric-list">
                    ${this.buildTextRow('Qualité dominante', data.qualite_air_dominante)}
                </div>
            </section>
        `;
    }

    buildLogementSocialGraph(data) {
        const items = [
            { label: 'Part logements sociaux', value: data.part_logements_sociaux_apur_pct },
            { label: 'Accessibilité', value: data.indice_accessibilite },
            { label: 'Tension sociale', value: data.indice_tension_sociale }
        ].filter(item => asNumber(item.value) !== null);

        if (!items.length && asNumber(data.nb_logements_sociaux_apur) === null && !data.estimation_logement_social_pct) {
            return '';
        }

        return `
            <section class="detail-section chart-section">
                <div class="section-head">
                    <h4>🏢 Logements sociaux</h4>
                    <span>APUR</span>
                </div>

                ${items.length ? `
                    <div class="chart-card">
                        ${this.horizontalBars(items, item => {
                            if (item.label.includes('Part')) return `${formatDecimal(item.value, 1)}%`;
                            return `${formatDecimal(item.value, 1)}/10`;
                        }, 10)}
                    </div>
                ` : ''}

                <div class="metric-list">
                    ${this.buildDetailRow('Nombre logements sociaux', data.nb_logements_sociaux_apur, formatNumber)}
                    ${this.buildDetailRow('Part logements sociaux', data.part_logements_sociaux_apur_pct, formatPercent)}
                    ${this.buildTextRow('Estimation', data.estimation_logement_social_pct)}
                </div>
            </section>
        `;
    }

    buildDemographieSection(data) {
        const rows = [
            this.buildDetailRow('Population 2022', data.population_2022, formatNumber),
            this.buildDetailRow('Ménages 2022', data.nb_menages_2022, formatNumber),
            this.buildDetailRow('Logements 2022', data.nb_logements_2022, formatNumber),
            this.buildDetailRow('Superficie', data.superficie_km2, v => `${formatDecimal(v, 2)} km²`),
            this.buildDetailRow('Densité population', data.densite_pop_km2, v => `${formatNumber(v)} hab/km²`),
            this.buildDetailRow('Revenu médian', data.revenu_median, formatPrice)
        ].filter(Boolean).join('');

        if (!rows) return '';

        return `
            <section class="detail-section">
                <h4>👥 Démographie & revenus</h4>
                <div class="metric-list">${rows}</div>
            </section>
        `;
    }

    buildIndicateursSection(data) {
        const scores = [
            {
                label: 'Accessibilité',
                value: data.indice_accessibilite,
                help: '10 = plus accessible',
                icon: '💸'
            },
            {
                label: 'Tension sociale',
                value: data.indice_tension_sociale,
                help: '10 = tension forte',
                icon: '⚖️'
            },
            {
                label: 'Attractivité',
                value: data.indice_attractivite,
                help: 'Transport + marché',
                icon: '🏙️'
            },
            {
                label: 'Pression immo',
                value: data.indice_pression_immo,
                help: 'Volume + évolution + T1',
                icon: '📉'
            }
        ].filter(item => asNumber(item.value) !== null);

        if (!scores.length && asNumber(data.ratio_effort_achat) === null) return '';

        return `
            <section class="detail-section score-section">
                <div class="section-head">
                    <h4>📊 Indices composites</h4>
                    <span>0 à 10</span>
                </div>

                <div class="score-grid">
                    ${scores.map(score => this.scoreCard(score)).join('')}

                    ${asNumber(data.ratio_effort_achat) !== null ? `
                        <div class="score-card effort-card">
                            <div class="score-card-top">
                                <span>🏦</span>
                                <strong>Effort achat</strong>
                            </div>
                            <div class="score-value">${formatDecimal(data.ratio_effort_achat, 1)} ans</div>
                            <small>Revenu médian pour acheter 50m²</small>
                        </div>
                    ` : ''}
                </div>
            </section>
        `;
    }

    scoreCard(item) {
        const value = asNumber(item.value);
        if (value === null) return '';

        const width = Math.max(0, Math.min(100, value * 10));

        return `
            <div class="score-card">
                <div class="score-card-top">
                    <span>${item.icon}</span>
                    <strong>${item.label}</strong>
                </div>
                <div class="score-value">${formatDecimal(value, 1)}/10</div>
                <div class="score-bar">
                    <i style="width:${width}%"></i>
                </div>
                <small>${item.help}</small>
            </div>
        `;
    }

    getYearSeries(data, prefix) {
        return [2020, 2021, 2022, 2023, 2024, 2025]
            .map(year => ({
                label: String(year),
                value: asNumber(data[`${prefix}_${year}`])
            }))
            .filter(item => item.value !== null);
    }

    getEvolutionSeries(data, prefix) {
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
                value: asNumber(data[key])
            }))
            .filter(item => item.value !== null);
    }

    buildDetailRow(label, value, formatter = formatNumber, trend = false) {
        const n = asNumber(value);
        if (n === null) return '';

        const formatted = formatter(value);
        const trendClass = trend ? (n <= 0 ? 'positive' : 'bad') : '';

        return `
            <div class="detail-row">
                <div class="row-left">
                    <span class="row-icon blue">•</span>
                    <span>${label}</span>
                </div>
                <div class="detail-value ${trendClass}">${formatted}</div>
            </div>
        `;
    }

    buildTextRow(label, value) {
        if (!hasValue(value)) return '';

        return `
            <div class="detail-row">
                <div class="row-left">
                    <span class="row-icon blue">•</span>
                    <span>${label}</span>
                </div>
                <div class="detail-value">${safeText(value)}</div>
            </div>
        `;
    }

    chartCard(title, subtitle, chart) {
        if (!chart) return '';

        return `
            <article class="chart-card">
                <div class="chart-card-head">
                    <strong>${title}</strong>
                    <small>${subtitle}</small>
                </div>
                ${chart}
            </article>
        `;
    }

    lineChart(items, formatter = formatNumber) {
        const values = items
            .map(item => asNumber(item.value))
            .filter(value => value !== null);

        if (values.length < 2) return '';

        const width = 420;
        const height = 170;
        const padX = 34;
        const padY = 24;

        let min = Math.min(...values);
        let max = Math.max(...values);

        if (min === max) {
            min -= 1;
            max += 1;
        }

        const range = max - min;
        const step = (width - padX * 2) / Math.max(1, values.length - 1);

        const points = values.map((value, index) => {
            const x = padX + step * index;
            const y = height - padY - ((value - min) / range) * (height - padY * 2);

            return {
                x,
                y,
                value,
                label: items[index].label
            };
        });

        const gradientId = `areaGradient-${Math.random().toString(36).slice(2)}`;

        const path = points
            .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
            .join(' ');

        const area = `${path} L ${points[points.length - 1].x.toFixed(1)} ${height - padY} L ${points[0].x.toFixed(1)} ${height - padY} Z`;

        return `
            <div class="line-chart-wrap">
                <svg class="line-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#2563eb" stop-opacity="0.20"></stop>
                            <stop offset="100%" stop-color="#2563eb" stop-opacity="0.00"></stop>
                        </linearGradient>
                    </defs>

                    <line class="grid-line" x1="${padX}" y1="${padY}" x2="${width - padX}" y2="${padY}"></line>
                    <line class="grid-line" x1="${padX}" y1="${height / 2}" x2="${width - padX}" y2="${height / 2}"></line>
                    <line class="grid-line" x1="${padX}" y1="${height - padY}" x2="${width - padX}" y2="${height - padY}"></line>

                    <path class="chart-area" d="${area}" fill="url(#${gradientId})"></path>
                    <path class="chart-line" d="${path}"></path>

                    ${points.map(point => `
                        <circle class="chart-dot" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="4">
                            <title>${point.label} · ${formatter(point.value)}</title>
                        </circle>
                    `).join('')}

                    ${points.map(point => `
                        <text class="chart-x-label" x="${point.x.toFixed(1)}" y="${height - 6}" text-anchor="middle">${point.label}</text>
                    `).join('')}
                </svg>

                <div class="chart-minmax">
                    <span>Min ${formatter(min)}</span>
                    <span>Max ${formatter(max)}</span>
                </div>
            </div>
        `;
    }

    horizontalBars(items, formatter, forcedMax = null) {
        const clean = items
            .map(item => ({
                ...item,
                value: asNumber(item.value)
            }))
            .filter(item => item.value !== null);

        if (!clean.length) return '';

        const max = forcedMax || Math.max(...clean.map(item => item.value)) || 1;

        return `
            <div class="bar-list">
                ${clean.map(item => {
                    const width = Math.max(2, Math.min(100, (item.value / max) * 100));

                    return `
                        <div class="bar-row">
                            <div class="bar-row-top">
                                <span>${item.label}</span>
                                <strong>${formatter(item)}</strong>
                            </div>
                            <div class="bar-track">
                                <i style="width:${width}%"></i>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    divergingBars(items) {
        const clean = items
            .map(item => ({
                ...item,
                value: asNumber(item.value)
            }))
            .filter(item => item.value !== null);

        if (!clean.length) return '';

        const maxAbs = Math.max(...clean.map(item => Math.abs(item.value))) || 1;

        return `
            <div class="diverging-list">
                ${clean.map(item => {
                    const positive = item.value >= 0;
                    const width = Math.max(4, Math.min(50, Math.abs(item.value) / maxAbs * 50));

                    return `
                        <div class="diverging-row">
                            <span>${item.label}</span>
                            <div class="diverging-track">
                                <i class="${positive ? 'positive-side' : 'negative-side'}"
                                   style="${positive ? `left:50%;width:${width}%` : `right:50%;width:${width}%`}"></i>
                            </div>
                            <strong class="${positive ? 'bad' : 'good'}">${formatPercent(item.value)}</strong>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    async updateStatsPanel(metric) {
        const statsContent = document.getElementById('stats-content');
        if (!statsContent) return;

        try {
            const response = await this.api.getAllArrondissements();
            const data = this.unwrapApiResponse(response);
            const list = Array.isArray(data)
                ? data
                : Array.isArray(data?.arrondissements)
                    ? data.arrondissements
                    : [];

            const year = document.getElementById('year-select')?.value || '2024';
            const metricKey = getYearAwareMetric(metric, year);

            const values = list
                .map(item => asNumber(item[metricKey]))
                .filter(value => value !== null);

            const info = getIndicatorDescription(metricKey);

            if (!values.length) {
                statsContent.innerHTML = `
                    <p>${info.text}</p>
                    <small>${info.source}</small>
                `;
                return;
            }

            const min = Math.min(...values);
            const max = Math.max(...values);
            const avg = values.reduce((sum, value) => sum + value, 0) / values.length;

            statsContent.innerHTML = `
                <div class="stat-mini-row">
                    <span>Minimum</span>
                    <b>${formatValueForMetric(min, metricKey)}</b>
                </div>
                <div class="stat-mini-row">
                    <span>Moyenne</span>
                    <b>${formatValueForMetric(avg, metricKey)}</b>
                </div>
                <div class="stat-mini-row">
                    <span>Maximum</span>
                    <b>${formatValueForMetric(max, metricKey)}</b>
                </div>
                <small>${info.source}</small>
            `;
        } catch (error) {
            log(`❌ Erreur stats: ${error.message}`, 'error');
        }
    }

    async updateKpiCards() {
    try {
        let rows = [];

        // 1) Essayer l'endpoint global
        try {
            const response = await this.api.getAllArrondissements();

            if (Array.isArray(response)) {
                rows = response;
            } else if (Array.isArray(response?.data)) {
                rows = response.data;
            } else if (Array.isArray(response?.arrondissements)) {
                rows = response.arrondissements;
            } else if (Array.isArray(response?.data?.arrondissements)) {
                rows = response.data.arrondissements;
            }
        } catch (error) {
            console.warn('Endpoint global KPI ignoré:', error);
        }

        // 2) Fallback sûr : récupérer les 20 arrondissements un par un
        if (!rows.length) {
            const jobs = [];

            for (let i = 1; i <= 20; i++) {
                jobs.push(
                    this.api.getArrondissement(i)
                        .then(response => response?.data || response)
                        .catch(() => null)
                );
            }

            rows = (await Promise.all(jobs)).filter(Boolean);
        }

        if (!rows.length) return;

        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el && hasValue(value)) {
                el.textContent = value;
            }
        };

        const getFirstNumber = (item, keys) => {
            for (const key of keys) {
                const n = asNumber(item?.[key]);
                if (n !== null) return n;
            }

            return 0;
        };

        setText('kpi-arrondissements', rows.length);

        const population = rows.reduce((sum, item) => {
            return sum + getFirstNumber(item, [
                'population_2022',
                'population',
                'population_2024'
            ]);
        }, 0);

        const logements = rows.reduce((sum, item) => {
            return sum + getFirstNumber(item, [
                'nb_logements_2022',
                'nb_logements',
                'logements_2022',
                'nb_appartements_2024',
                'nb_appartement_2024'
            ]);
        }, 0);

        const prixM2 = rows
            .map(item => getFirstNumber(item, [
                'prix_m2_median_2024',
                'prix_m2_moyen_2024',
                'prix_m2_median',
                'prix_m2'
            ]))
            .filter(value => value > 0);

        if (population > 0) {
            setText('kpi-population', formatCompact(population));
        }

        if (logements > 0) {
            setText('kpi-logements', formatCompact(logements));
        }

        if (prixM2.length) {
            const avgPrixM2 = prixM2.reduce((sum, value) => sum + value, 0) / prixM2.length;
            setText('kpi-marche', formatPricePerM2(avgPrixM2));
        }

        console.log('✅ KPI mis à jour', {
            arrondissements: rows.length,
            population,
            logements,
            prixM2
        });
    } catch (error) {
        log(`⚠️ KPI non mis à jour: ${error.message}`, 'warning');
        console.warn(error);
    }
}

    showError(message) {
        const detailContent = document.getElementById('detail-content');

        if (detailContent) {
            detailContent.innerHTML = `
                <div class="empty-detail">
                    <strong>⚠️ ${message}</strong>
                    <p>Vérifie que l’API Flask tourne bien sur http://localhost:5000/api.</p>
                </div>
            `;
        }
    }
}

function closeDetailPanel() {
    const panel = document.getElementById('detail-panel');
    if (panel) panel.classList.add('hidden');
}