(() => {
    'use strict';

    window.switchTab = function switchTab(tabName, evt) {
        const contents = document.querySelectorAll('.tab-content');
        contents.forEach((content) => content.classList.remove('active'));

        const tabs = document.querySelectorAll('.tab');
        tabs.forEach((tab) => tab.classList.remove('active'));

        const selectedSection = document.getElementById(tabName);
        if (selectedSection) {
            selectedSection.classList.add('active');
        }

        const target = evt?.currentTarget || evt?.target || window.event?.target;
        if (target) {
            target.classList.add('active');
        }
    };
    
    const API_BASE_URL = 'http://localhost:8000';

    document.addEventListener('DOMContentLoaded', () => {
        initializeMap();
        initializeDashboardFilters();
    });

    function initializeMap() {
        const mapContainer = document.getElementById('map');
        const infoBox = document.getElementById('info');

        if (!mapContainer) {
            console.warn('Le conteneur de carte est introuvable.');
            return;
        }

        const defaultInfo = `
            <h4>Arrondissements de Paris</h4>
            <p>Survolez un arrondissement</p>
        `;

        if (infoBox) {
            infoBox.innerHTML = defaultInfo;
        }

        const map = new maplibregl.Map({
            container: 'map',
            style: 'https://tiles.openfreemap.org/styles/bright',
            center: [2.3522, 48.8566],
            zoom: 11
        });

        map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

        let hoveredId = null;

        map.on('load', () => {
            fetch(`${API_BASE_URL}/api/arrondissements.geojson`)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error('Impossible de charger le GeoJSON local');
                    }
                    return response.json();
                })
                .then((geojsonData) => {
                    geojsonData.features.forEach((feature, index) => {
                        feature.id = index;
                        feature.properties.value = Math.random() * 25;
                    });

                    map.addSource('arrondissements', {
                        type: 'geojson',
                        data: geojsonData,
                        promoteId: 'id'
                    });

                    map.addLayer({
                        id: 'arrondissements-fill',
                        type: 'fill',
                        source: 'arrondissements',
                        paint: {
                            'fill-color': [
                                'step',
                                ['get', 'value'],
                                '#FFEDA0', 2,
                                '#FED976', 4,
                                '#FEB24C', 6,
                                '#FD8D3C', 8,
                                '#FC4E2A', 10,
                                '#E31A1C', 15,
                                '#BD0026', 20,
                                '#800026'
                            ],
                            'fill-opacity': [
                                'case',
                                ['boolean', ['feature-state', 'hover'], false],
                                0.9,
                                0.7
                            ]
                        }
                    });

                    map.addLayer({
                        id: 'arrondissements-outline',
                        type: 'line',
                        source: 'arrondissements',
                        paint: {
                            'line-color': '#ffffff',
                            'line-width': [
                                'case',
                                ['boolean', ['feature-state', 'hover'], false],
                                4,
                                2
                            ]
                        }
                    });

                    map.on('mousemove', 'arrondissements-fill', (e) => {
                        if (!e.features || !e.features.length) {
                            return;
                        }

                        if (hoveredId !== null) {
                            map.setFeatureState(
                                { source: 'arrondissements', id: hoveredId },
                                { hover: false }
                            );
                        }

                        hoveredId = e.features[0].id;

                        map.setFeatureState(
                            { source: 'arrondissements', id: hoveredId },
                            { hover: true }
                        );

                        const props = e.features[0].properties;
                        if (infoBox) {
                            infoBox.innerHTML = `
                                <h4>${props.libgeo || 'Arrondissement'}</h4>
                                <p><strong>Valeur:</strong> ${props.value ? props.value.toFixed(2) : 'N/A'}</p>
                            `;
                        }

                        map.getCanvas().style.cursor = 'pointer';
                    });

                    map.on('mouseleave', 'arrondissements-fill', () => {
                        if (hoveredId !== null) {
                            map.setFeatureState(
                                { source: 'arrondissements', id: hoveredId },
                                { hover: false }
                            );
                        }
                        hoveredId = null;

                        if (infoBox) {
                            infoBox.innerHTML = defaultInfo;
                        }

                        map.getCanvas().style.cursor = '';
                    });

                    map.on('click', 'arrondissements-fill', (e) => {
                        if (!e.features || !e.features.length) {
                            return;
                        }

                        const feature = e.features[0];
                        const bounds = new maplibregl.LngLatBounds();

                        if (feature.geometry.type === 'Polygon') {
                            feature.geometry.coordinates[0].forEach((coord) => bounds.extend(coord));
                        } else if (feature.geometry.type === 'MultiPolygon') {
                            feature.geometry.coordinates.forEach((polygon) => {
                                polygon[0].forEach((coord) => bounds.extend(coord));
                            });
                        }

                        map.fitBounds(bounds, { padding: 40, duration: 800 });
                    });
                })
                .catch((error) => {
                    console.error(error);
                    if (infoBox) {
                        infoBox.innerHTML = `
                            <h4>Erreur</h4>
                            <p>${error.message}</p>
                            <p style="font-size: 12px;">Assurez-vous que le fichier arrondissements.geojson est dans le même répertoire.</p>
                        `;
                    }
                });
        });
    }

    function initializeDashboardFilters() {
        const yearSelect = document.getElementById('year-select');
        const arrondissementSelect = document.getElementById('arrondissement-select');

        if (!yearSelect || !arrondissementSelect) {
            return;
        }

        const state = {
            year: yearSelect.value,
            arrondissement: arrondissementSelect.value || 'all'
        };

        const refreshMetrics = () => {
            loadMetrics(state.year, state.arrondissement);
        };

        yearSelect.addEventListener('change', (event) => {
            state.year = event.target.value;
            refreshMetrics();
        });

        arrondissementSelect.addEventListener('change', (event) => {
            state.arrondissement = event.target.value || 'all';
            refreshMetrics();
        });

        refreshMetrics();
    }

    async function loadMetrics(year, arrondissement) {
        setMetricsLoading();
        try {
            const url = new URL(`${API_BASE_URL}/api/metrics`);
            url.searchParams.set('year', year);
            url.searchParams.set('arrondissement', arrondissement);
            const response = await fetch(url);
            if (!response.ok) {
                const errorPayload = await response.json().catch(() => ({}));
                throw new Error(errorPayload.error || 'Réponse serveur invalide');
            }
            const data = await response.json();
            renderMetrics(data);
        } catch (error) {
            console.error(error);
            renderMetricsError();
        }
    }

    function setMetricsLoading() {
        const ids = [
            'median-price-value',
            'social-housing-value',
            'median-income-value',
            'population-density-value',
            'air-quality-value'
        ];
        ids.forEach((id) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Chargement...';
            }
        });
        const changeElement = document.getElementById('median-price-change');
        if (changeElement) {
            changeElement.textContent = '';
            changeElement.classList.remove('negative');
        }
    }

    function renderMetrics(data) {
        updatePriceCard(data);
        updateSocialHousingCard(data);
        updateIncomeCard(data);
        updateDensityCard(data);
        updateAirQualityCard(data);
    }

    function renderMetricsError() {
        const ids = [
            'median-price-value',
            'social-housing-value',
            'median-income-value',
            'population-density-value',
            'air-quality-value'
        ];
        ids.forEach((id) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Donnée indisponible';
            }
        });
        const changeElement = document.getElementById('median-price-change');
        if (changeElement) {
            changeElement.textContent = 'Comparaison indisponible';
            changeElement.classList.add('negative');
        }
    }

    function updatePriceCard(data) {
        const priceValue = document.getElementById('median-price-value');
        if (priceValue) {
            priceValue.textContent = formatCurrency(data.prix_m2_median);
        }

        const changeElement = document.getElementById('median-price-change');
        if (!changeElement) {
            return;
        }

        if (typeof data.variation === 'number' && Number.isFinite(data.variation)) {
            const symbol = data.variation > 0 ? '↑' : data.variation < 0 ? '↓' : '→';
            const sign = data.variation > 0 ? '+' : '';
            changeElement.textContent = `${symbol} ${sign}${data.variation.toFixed(2)}% vs ${data.year - 1}`;
            changeElement.classList.toggle('negative', data.variation < 0);
        } else {
            changeElement.textContent = 'Comparaison indisponible';
            changeElement.classList.remove('negative');
        }
    }

    function updateSocialHousingCard(data) {
        const element = document.getElementById('social-housing-value');
        if (element) {
            element.textContent = formatPercent(data.tx_logement_sociaux);
        }
    }

    function updateIncomeCard(data) {
        const element = document.getElementById('median-income-value');
        if (element) {
            element.textContent = formatCurrency(data.revenu_median);
        }
    }

    function updateDensityCard(data) {
        const element = document.getElementById('population-density-value');
        if (element) {
            element.textContent = formatDensity(data.densite_population);
        }
    }

    function updateAirQualityCard(data) {
        const element = document.getElementById('air-quality-value');
        if (element) {
            element.textContent = data.air_quality_global || 'N/A';
        }
    }

    function formatCurrency(value) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            return 'N/A';
        }
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            maximumFractionDigits: 0
        }).format(value);
    }

    function formatPercent(value) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            return 'N/A';
        }
        return `${value.toFixed(1)}%`;
    }

    function formatDensity(value) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            return 'N/A';
        }
        const formatted = new Intl.NumberFormat('fr-FR', {
            maximumFractionDigits: 0
        }).format(value);
        return `${formatted} hab/km²`;
    }
})();
