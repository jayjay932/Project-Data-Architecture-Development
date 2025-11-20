/**
 * Gestion de la carte MapLibre
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
        
        this.GEOJSON_URL = 'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson?lang=fr&timezone=Europe%2FParis';
    }

    async init() {
        try {
            log('🗺️  Initialisation de la carte...', 'info');
            
            // Créer la carte MapLibre
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

            // Ajouter contrôles de navigation
            this.map.addControl(new maplibregl.NavigationControl(), 'top-right');

            // Attendre que la carte soit chargée
            await new Promise(resolve => this.map.on('load', resolve));

            // Charger les données
            await this.loadData();
            await this.loadGeoJSON();
            
            // Ajouter les couches
            this.addLayers();
            
            // Ajouter les interactions
            this.addInteractions();
            
            log('✅ Carte initialisée', 'success');
        } catch (error) {
            log(`❌ Erreur initialisation carte: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadData() {
        try {
            log('📊 Chargement des données...', 'info');
            
            for (let i = 1; i <= 20; i++) {
                try {
                    const data = await this.api.getArrondissement(i);
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
            
            // Normaliser les propriétés
            this.geojson.features.forEach(feature => {
                const raw = feature.properties.c_ar || 
                           feature.properties.numero || 
                           feature.properties.ar;
                
                feature.properties.numero = String(raw).replace(/^0/, '');
                feature.properties.nom = feature.properties.l_aroff || 
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
        // Source GeoJSON
        this.map.addSource('arrondissements', {
            type: 'geojson',
            data: this.geojson,
            promoteId: 'numero'
        });

        // Couche de remplissage
        this.map.addLayer({
            id: 'arr-fill',
            type: 'fill',
            source: 'arrondissements',
            paint: {
                'fill-color': this.buildColorExpression(),
                'fill-opacity': 0.75
            }
        });

        // Couche de contour
        this.map.addLayer({
            id: 'arr-line',
            type: 'line',
            source: 'arrondissements',
            paint: {
                'line-color': '#333',
                'line-width': [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    3,
                    1.5
                ],
                'line-opacity': 0.8
            }
        });

        // Labels (numéros)
        this.map.addLayer({
            id: 'arr-labels',
            type: 'symbol',
            source: 'arrondissements',
            layout: {
                'text-field': ['get', 'numero'],
                'text-size': 16
            },
            paint: {
                'text-color': '#000',
                'text-halo-color': '#fff',
                'text-halo-width': 2.5
            }
        });
        
        log('✅ Couches ajoutées', 'success');
    }

    buildColorExpression() {
        const expr = ['match', ['to-string', ['get', 'numero']]];
        
        this.geojson.features.forEach(feature => {
            const numero = String(feature.properties.numero);
            const arrData = this.data.get(parseInt(numero));
            
            if (arrData) {
                const value = this.getMetricValue(arrData);
                const color = getColorForValue(value, this.currentMetric);
                expr.push(numero, color);
            }
        });
        
        expr.push('#e0e0e0'); // Couleur par défaut
        return expr;
    }

    getMetricValue(data) {
        // Adapter la métrique avec l'année si nécessaire
        let metric = this.currentMetric;
        
        // Si la métrique contient une année (ex: prix_m2_median_2024)
        if (/_\d{4}$/.test(metric)) {
            // Remplacer l'année par celle sélectionnée
            metric = metric.replace(/_\d{4}$/, `_${this.currentYear}`);
        }
        
        return data[metric];
    }

    addInteractions() {
        // Survol
        this.map.on('mousemove', 'arr-fill', (e) => {
            if (e.features.length > 0) {
                // Retirer le survol précédent
                if (this.hoveredId !== null) {
                    this.map.setFeatureState(
                        { source: 'arrondissements', id: this.hoveredId },
                        { hover: false }
                    );
                }
                
                this.hoveredId = e.features[0].properties.numero;
                
                // Appliquer le survol
                this.map.setFeatureState(
                    { source: 'arrondissements', id: this.hoveredId },
                    { hover: true }
                );
                
                // Afficher tooltip
                this.showTooltip(e, e.features[0]);
            }
        });

        // Quitter le survol
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

        // Clic
        this.map.on('click', 'arr-fill', (e) => {
            if (e.features.length > 0) {
                const numero = parseInt(e.features[0].properties.numero);
                this.onArrondissementClick(numero);
            }
        });

        // Curseur pointer
        this.map.on('mouseenter', 'arr-fill', () => {
            this.map.getCanvas().style.cursor = 'pointer';
        });

        this.map.on('mouseleave', 'arr-fill', () => {
            this.map.getCanvas().style.cursor = '';
        });
    }

    showTooltip(e, feature) {
        const numero = parseInt(feature.properties.numero);
        const data = this.data.get(numero);
        
        if (!data) return;
        
        const value = this.getMetricValue(data);
        const formattedValue = formatValueForMetric(value, this.currentMetric);
        
        // Construire le contenu selon la métrique
        let extraInfo = '';
        
        // ========================================
        // TRANSPORT : Afficher les lignes
        // ========================================
        if (this.currentMetric.includes('metro') || 
            this.currentMetric.includes('station') || 
            this.currentMetric.includes('ligne') || 
            this.currentMetric.includes('trafic')) {
            
            const lignesMetro = this.parseLignes(data.lignes_metro);
            const lignesRER = this.parseLignes(data.lignes_rer);
            const nbStations = data.nb_stations_metro;
            const trafic = data.trafic_total_metro;
            
            extraInfo += '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.3);">';
            
            if (nbStations) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>📍 Stations:</strong> ${nbStations}</p>`;
            }
            
            if (lignesMetro.length > 0) {
                const badges = lignesMetro.map(l => 
                    `<span style="background: #667eea; padding: 0.15rem 0.4rem; border-radius: 3px; margin: 0 0.2rem; font-weight: bold; font-size: 0.8rem;">${l}</span>`
                ).join('');
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>🚇 Métro:</strong><br/>${badges}</p>`;
            }
            
            if (lignesRER.length > 0) {
                const badges = lignesRER.map(l => 
                    `<span style="background: #22c55e; padding: 0.15rem 0.4rem; border-radius: 3px; margin: 0 0.2rem; font-weight: bold; font-size: 0.8rem;">${l}</span>`
                ).join('');
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>🚊 RER:</strong><br/>${badges}</p>`;
            }
            
            if (trafic) {
                extraInfo += `<p style="margin: 0.25rem 0;"><strong>👥 Trafic:</strong> ${formatNumber(trafic)} pass./an</p>`;
            }
            
            extraInfo += '</div>';
        }
        
        // ========================================
        // LOGEMENTS SOCIAUX : Afficher APUR + estimation
        // ========================================
        if (this.currentMetric.includes('logement') || 
            this.currentMetric.includes('social') ||
            this.currentMetric.includes('apur')) {
            
            const nbApur = data.nb_logements_sociaux_apur;
            const pctApur = data.part_logements_sociaux_apur_pct;
            const estimation = data.estimation_logement_social_pct;
            
            extraInfo += '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.3);">';
            
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
        
        // ========================================
        // PRIX : Afficher évolution
        // ========================================
        if (this.currentMetric.includes('prix') && !this.currentMetric.includes('evolution')) {
            const evolution = data.evolution_prix_2020_2024_pct;
            if (evolution !== null && evolution !== undefined) {
                const icon = evolution > 0 ? '📈' : evolution < 0 ? '📉' : '➡️';
                const color = evolution > 0 ? '#22c55e' : evolution < 0 ? '#ef4444' : '#94a3b8';
                extraInfo += `<p style="margin-top: 0.5rem; color: ${color};"><strong>${icon} Évolution 2020-2024:</strong> ${formatPercent(evolution)}</p>`;
            }
        }
        
        // ========================================
        // POLLUTION : Afficher qualité dominante
        // ========================================
        if (this.currentMetric.includes('no2') || 
            this.currentMetric.includes('pm10') || 
            this.currentMetric.includes('o3') ||
            this.currentMetric.includes('air')) {
            
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
                <p style="font-size: 1.1rem; font-weight: bold; color: #fbbf24;">${formattedValue}</p>
                ${extraInfo}
            `;
            tooltip.style.left = `${e.point.x + 10}px`;
            tooltip.style.top = `${e.point.y + 10}px`;
            tooltip.classList.add('visible');
        }
    }
    
    parseLignes(lignesStr) {
        // Parse les lignes de transport depuis le format CSV
        if (!lignesStr || lignesStr === 'null' || lignesStr === '') {
            return [];
        }
        
        // Enlever les espaces et split par virgule
        const lignes = lignesStr.split(',').map(l => l.trim());
        
        // Nettoyer les doublons et les valeurs invalides
        const lignesClean = [...new Set(lignes)]
            .filter(l => l && l !== '0' && l !== 'null')
            .map(l => {
                // Enlever les .0 (ex: "11.0" -> "11")
                if (l.endsWith('.0')) {
                    return l.slice(0, -2);
                }
                return l;
            });
        
        // Trier: chiffres d'abord, puis lettres
        const chiffres = lignesClean.filter(l => /^\d+$/.test(l)).sort((a, b) => parseInt(a) - parseInt(b));
        const lettres = lignesClean.filter(l => /^[A-Z]$/.test(l)).sort();
        
        return [...chiffres, ...lettres];
    }

    onArrondissementClick(numero) {
        log(`📍 Clic sur arrondissement ${numero}`, 'info');
        
        // Événement personnalisé pour le panneau de détails
        window.dispatchEvent(new CustomEvent('arrondissement-selected', {
            detail: { numero }
        }));
    }

    async updateMetric(metric, year) {
        this.currentMetric = metric;
        this.currentYear = year;
        
        log(`🔄 Mise à jour: ${metric}, année ${year}`, 'info');
        
        // Recharger les données si nécessaire
        await this.loadData();
        
        // Mettre à jour les couleurs
        if (this.map.getLayer('arr-fill')) {
            this.map.setPaintProperty('arr-fill', 'fill-color', this.buildColorExpression());
        }
        
        // Mettre à jour la légende
        this.updateLegend();
        
        log('✅ Carte mise à jour', 'success');
    }

    updateLegend() {
        // Récupérer toutes les valeurs de la métrique
        const values = [];
        this.data.forEach(data => {
            const value = this.getMetricValue(data);
            if (value !== null && value !== undefined) {
                values.push(value);
            }
        });
        
        // Créer l'échelle
        const scale = createLegendScale(values, this.currentMetric);
        
        // Mettre à jour le DOM
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

// Fonction helper pour masquer le tooltip
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
    }
}