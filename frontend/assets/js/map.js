/**
 * Gestion de la carte MapLibre
 * Version stable :
 * - basée sur ta version qui marchait
 * - pas de glyphs / pas de text-font MapLibre
 * - numéros d'arrondissements affichés par défaut avec des markers HTML
 * - selectArrondissement ajouté pour éviter l'erreur main.js
 */

class ParisMap {
    constructor(containerId, api) {
        this.containerId = containerId;
        this.api = api;
        this.map = null;
        this.currentMetric = 'prix_m2_median_2024';
        this.currentYear = '2024';
        this.data = new Map();
        this.geojson = null;
        this.hoveredId = null;
        this.selectedId = null;
        this.labelMarkers = [];

        this.GEOJSON_URL = 'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson?lang=fr&timezone=Europe%2FParis';
    }

    async init() {
        try {
            log('🗺️  Initialisation de la carte...', 'info');

            this.map = new maplibregl.Map({
                container: this.containerId,
                style: {
                    version: 8,
                    sources: {
                        'osm-raster': {
                            type: 'raster',
                            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                            tileSize: 256,
                            attribution: '© OpenStreetMap'
                        }
                    },
                    layers: [{
                        id: 'osm-base',
                        type: 'raster',
                        source: 'osm-raster'
                    }]
                },
                center: [2.3522, 48.8566],
                zoom: 11.5,
                maxZoom: 18,
                minZoom: 10
            });

            this.map.addControl(new maplibregl.NavigationControl(), 'top-right');

            await new Promise(resolve => this.map.on('load', resolve));

            await this.loadData();
            await this.loadGeoJSON();

            this.addLayers();
            this.addInteractions();
            this.addDefaultLabels();
            this.updateLegend();

            log('✅ Carte initialisée', 'success');
        } catch (error) {
            log(`❌ Erreur initialisation carte: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadData() {
        try {
            log('📊 Chargement des données...', 'info');

            this.data.clear();

            for (let i = 1; i <= 20; i++) {
                try {
                    const response = await this.api.getArrondissement(i);
                    const data = response?.data || response;
                    this.data.set(i, data);
                } catch (error) {
                    log(`⚠️  Impossible de charger arrondissement ${i}`, 'warning');
                }
            }

            log(`✅ ${this.data.size} arrondissements chargés`, 'success');
        } catch (error) {
            log(`❌ Erreur chargement données: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadGeoJSON() {
        try {
            log('🗺️  Chargement GeoJSON...', 'info');

            const response = await fetch(this.GEOJSON_URL);
            this.geojson = await response.json();

            this.geojson.features.forEach(feature => {
                const raw =
                    feature.properties.c_ar ||
                    feature.properties.C_AR ||
                    feature.properties.numero ||
                    feature.properties.ar;

                feature.properties.numero = String(raw).replace(/^0/, '');
                feature.properties.nom =
                    feature.properties.l_aroff ||
                    feature.properties.nom ||
                    `${feature.properties.numero}e`;
            });

            log('✅ GeoJSON chargé', 'success');
        } catch (error) {
            log(`❌ Erreur GeoJSON: ${error.message}`, 'error');
            throw error;
        }
    }

    addLayers() {
        this.map.addSource('arrondissements', {
            type: 'geojson',
            data: this.geojson,
            promoteId: 'numero'
        });

        this.map.addLayer({
            id: 'arr-fill',
            type: 'fill',
            source: 'arrondissements',
            paint: {
                'fill-color': this.buildColorExpression(),
                'fill-opacity': [
                    'case',
                    ['boolean', ['feature-state', 'selected'], false], 0.9,
                    ['boolean', ['feature-state', 'hover'], false], 0.85,
                    0.75
                ]
            }
        });

        this.map.addLayer({
            id: 'arr-line',
            type: 'line',
            source: 'arrondissements',
            paint: {
                'line-color': [
                    'case',
                    ['boolean', ['feature-state', 'selected'], false], '#064e3b',
                    ['boolean', ['feature-state', 'hover'], false], '#15803d',
                    '#333333'
                ],
                'line-width': [
                    'case',
                    ['boolean', ['feature-state', 'selected'], false], 4,
                    ['boolean', ['feature-state', 'hover'], false], 3,
                    1.5
                ],
                'line-opacity': 0.85
            }
        });

        log('✅ Couches ajoutées', 'success');
    }

    buildColorExpression() {
        const expr = ['match', ['to-string', ['get', 'numero']]];

        this.geojson.features.forEach(feature => {
            const numero = String(feature.properties.numero);
            const arrData = this.data.get(parseInt(numero, 10));

            if (arrData) {
                const value = this.getMetricValue(arrData);
                const color = getColorForValue(value, this.currentMetric);
                expr.push(numero, color);
            }
        });

        expr.push('#e0e0e0');

        return expr;
    }

    getMetricValue(data) {
        let metric = this.currentMetric;

        if (/_\d{4}$/.test(metric)) {
            metric = metric.replace(/_\d{4}$/, `_${this.currentYear}`);
        }

        return data ? data[metric] : null;
    }

    addDefaultLabels() {
        this.clearDefaultLabels();

        if (!this.geojson || !Array.isArray(this.geojson.features)) return;

        this.geojson.features.forEach(feature => {
            const numero = feature.properties.numero;
            const center = this.getFeatureCenter(feature);

            if (!center) return;

            const el = document.createElement('div');
            el.textContent = `${numero}e`;
            el.style.width = '42px';
            el.style.height = '42px';
            el.style.borderRadius = '999px';
            el.style.display = 'flex';
            el.style.alignItems = 'center';
            el.style.justifyContent = 'center';
            el.style.background = 'rgba(255, 255, 255, 0.92)';
            el.style.border = '2px solid rgba(6, 78, 59, 0.42)';
            el.style.color = '#064e3b';
            el.style.fontWeight = '900';
            el.style.fontSize = '15px';
            el.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.15)';
            el.style.pointerEvents = 'none';
            el.style.backdropFilter = 'blur(8px)';

            const marker = new maplibregl.Marker({
                element: el,
                anchor: 'center'
            })
                .setLngLat(center)
                .addTo(this.map);

            this.labelMarkers.push(marker);
        });
    }

    clearDefaultLabels() {
        this.labelMarkers.forEach(marker => marker.remove());
        this.labelMarkers = [];
    }

    getFeatureCenter(feature) {
        try {
            const coords = [];

            const collect = (arr) => {
                if (!Array.isArray(arr)) return;

                if (
                    arr.length >= 2 &&
                    typeof arr[0] === 'number' &&
                    typeof arr[1] === 'number'
                ) {
                    coords.push(arr);
                    return;
                }

                arr.forEach(collect);
            };

            collect(feature.geometry.coordinates);

            if (!coords.length) return null;

            const bounds = new maplibregl.LngLatBounds();

            coords.forEach(coord => {
                bounds.extend(coord);
            });

            return bounds.getCenter();
        } catch (error) {
            return null;
        }
    }

    addInteractions() {
        this.map.on('mousemove', 'arr-fill', (e) => {
            if (e.features.length > 0) {
                if (this.hoveredId !== null) {
                    this.map.setFeatureState(
                        { source: 'arrondissements', id: this.hoveredId },
                        { hover: false }
                    );
                }

                this.hoveredId = e.features[0].properties.numero;

                this.map.setFeatureState(
                    { source: 'arrondissements', id: this.hoveredId },
                    { hover: true }
                );

                this.showTooltip(e, e.features[0]);
            }
        });

        this.map.on('mouseleave', 'arr-fill', () => {
            if (this.hoveredId !== null) {
                this.map.setFeatureState(
                    { source: 'arrondissements', id: this.hoveredId },
                    { hover: false }
                );
            }

            this.hoveredId = null;
            hideTooltip();
        });

        this.map.on('click', 'arr-fill', (e) => {
            if (e.features.length > 0) {
                const numero = parseInt(e.features[0].properties.numero, 10);
                this.selectArrondissement(numero);
                this.onArrondissementClick(numero);
            }
        });

        this.map.on('mouseenter', 'arr-fill', () => {
            this.map.getCanvas().style.cursor = 'pointer';
        });

        this.map.on('mouseleave', 'arr-fill', () => {
            this.map.getCanvas().style.cursor = '';
        });
    }

    selectArrondissement(numero) {
        if (!this.map || !this.map.getSource('arrondissements')) return;

        const id = String(numero);

        if (this.selectedId !== null) {
            this.map.setFeatureState(
                { source: 'arrondissements', id: this.selectedId },
                { selected: false }
            );
        }

        this.selectedId = id;

        this.map.setFeatureState(
            { source: 'arrondissements', id },
            { selected: true }
        );
    }

    showTooltip(e, feature) {
        const numero = parseInt(feature.properties.numero, 10);
        const data = this.data.get(numero);

        if (!data) return;

        const value = this.getMetricValue(data);
        const formattedValue = formatValueForMetric(value, this.currentMetric);

        let extraInfo = '';

        if (
            this.currentMetric.includes('metro') ||
            this.currentMetric.includes('station') ||
            this.currentMetric.includes('ligne') ||
            this.currentMetric.includes('trafic')
        ) {
            const lignesMetro = this.parseLignes(data.lignes_metro);
            const lignesRER = this.parseLignes(data.lignes_rer);
            const nbStations = data.nb_stations_metro;
            const trafic = data.trafic_total_metro;

            extraInfo += '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.08);">';

            if (nbStations) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>📍 Stations:</strong> ${nbStations}</p>`;
            }

            if (lignesMetro.length > 0) {
                const badges = lignesMetro.map(l =>
                    `<span style="background: #16a34a; color: white; padding: 0.15rem 0.4rem; border-radius: 3px; margin: 0 0.2rem; font-weight: bold; font-size: 0.8rem;">${l}</span>`
                ).join('');

                extraInfo += `<p style="margin: 0.25rem 0;"><strong>🚇 Métro:</strong><br/>${badges}</p>`;
            }

            if (lignesRER.length > 0) {
                const badges = lignesRER.map(l =>
                    `<span style="background: #0f766e; color: white; padding: 0.15rem 0.4rem; border-radius: 3px; margin: 0 0.2rem; font-weight: bold; font-size: 0.8rem;">${l}</span>`
                ).join('');

                extraInfo += `<p style="margin: 0.25rem 0;"><strong>🚊 RER:</strong><br/>${badges}</p>`;
            }

            if (trafic) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>👥 Trafic:</strong> ${formatNumber(trafic)} pass./an</p>`;
            }

            extraInfo += '</div>';
        }

        if (
            this.currentMetric.includes('logement') ||
            this.currentMetric.includes('social') ||
            this.currentMetric.includes('apur')
        ) {
            const nbApur = data.nb_logements_sociaux_apur;
            const pctApur = data.part_logements_sociaux_apur_pct;
            const estimation = data.estimation_logement_social_pct;

            extraInfo += '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.08);">';

            if (nbApur && nbApur > 0) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>🏢 APUR:</strong> ${formatNumber(nbApur)} logements</p>`;
            }

            if (pctApur && pctApur > 0) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>📊 Part:</strong> ${pctApur}%</p>`;
            }

            if (estimation) {
                const icon = estimation.includes('Élevé') ? '🟢' :
                             estimation.includes('Moyen') ? '🟡' : '🔴';

                extraInfo += `<p style="margin: 0.25rem 0;"><strong>${icon} Estimation:</strong> ${estimation}</p>`;
            }

            extraInfo += '</div>';
        }

        if (this.currentMetric.includes('prix') && !this.currentMetric.includes('evolution')) {
            const evolution = data.evolution_prix_2020_2024_pct;

            if (evolution !== null && evolution !== undefined) {
                const icon = evolution > 0 ? '📈' : evolution < 0 ? '📉' : '➡️';
                const color = evolution > 0 ? '#16a34a' : evolution < 0 ? '#ef4444' : '#64748b';

                extraInfo += `<p style="margin-top: 0.5rem; color: ${color};"><strong>${icon} Évolution 2020-2024:</strong> ${formatPercent(evolution)}</p>`;
            }
        }

        if (
            this.currentMetric.includes('no2') ||
            this.currentMetric.includes('pm10') ||
            this.currentMetric.includes('o3') ||
            this.currentMetric.includes('air')
        ) {
            const qualite = data.qualite_air_dominante;

            if (qualite) {
                extraInfo += `<p style="margin-top: 0.5rem;"><strong>🌫️ Qualité air:</strong> ${qualite}</p>`;
            }
        }

        const tooltip = document.getElementById('tooltip');

        if (tooltip) {
            tooltip.innerHTML = `
                <h5>${numero}e arrondissement</h5>
                <p><strong>${getMetricLabel(this.currentMetric)}:</strong></p>
                <p style="font-size: 1.1rem; font-weight: bold; color: #15803d;">${formattedValue}</p>
                ${extraInfo}
            `;

            tooltip.style.left = `${e.point.x + 10}px`;
            tooltip.style.top = `${e.point.y + 10}px`;
            tooltip.classList.add('visible');
        }
    }

    parseLignes(lignesStr) {
        if (!lignesStr || lignesStr === 'null' || lignesStr === '') {
            return [];
        }

        const lignes = lignesStr.split(',').map(l => l.trim());

        const lignesClean = [...new Set(lignes)]
            .filter(l => l && l !== '0' && l !== 'null')
            .map(l => {
                if (l.endsWith('.0')) {
                    return l.slice(0, -2);
                }

                return l;
            });

        const chiffres = lignesClean
            .filter(l => /^\d+$/.test(l))
            .sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

        const lettres = lignesClean
            .filter(l => /^[A-Z]$/.test(l))
            .sort();

        return [...chiffres, ...lettres];
    }

    onArrondissementClick(numero) {
        log(`📍 Clic sur arrondissement ${numero}`, 'info');

        window.dispatchEvent(
            new CustomEvent('arrondissement-selected', {
                detail: { numero }
            })
        );
    }

    async updateMetric(metric, year) {
        this.currentMetric = metric;
        this.currentYear = year;

        log(`🔄 Mise à jour: ${metric}, année ${year}`, 'info');

        await this.loadData();

        if (this.map.getLayer('arr-fill')) {
            this.map.setPaintProperty('arr-fill', 'fill-color', this.buildColorExpression());
        }

        this.updateLegend();

        log('✅ Carte mise à jour', 'success');
    }

    updateLegend() {
        const values = [];

        this.data.forEach(data => {
            const value = this.getMetricValue(data);

            if (value !== null && value !== undefined) {
                values.push(value);
            }
        });

        const scale = createLegendScale(values, this.currentMetric);

        const legendTitle = document.getElementById('legend-title');
        const legendScale = document.getElementById('legend-scale');

        if (legendTitle) {
            legendTitle.textContent = getMetricLabel(this.currentMetric);
        }

        if (legendScale) {
            legendScale.innerHTML = scale.map(item => `
                <div class="legend-item">
                    <div class="legend-color" style="background-color: ${item.color}"></div>
                    <span>${item.label}</span>
                </div>
            `).join('');
        }
    }
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');

    if (tooltip) {
        tooltip.classList.remove('visible');
    }
}