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
        initializeMedianPriceFilter();
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

    function initializeMedianPriceFilter() {
        const yearSelect = document.getElementById('year-select');
        const priceValue = document.getElementById('median-price-value');

        if (!yearSelect || !priceValue) {
            return;
        }

        const formatPrice = (value) =>
            new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'EUR',
                maximumFractionDigits: 0
            }).format(value);

        const updatePrice = async (year) => {
            priceValue.textContent = 'Chargement...';
            try {
                const response = await fetch(`${API_BASE_URL}/api/price?year=${encodeURIComponent(year)}`);
                if (!response.ok) {
                    const errorPayload = await response.json().catch(() => ({}));
                    throw new Error(errorPayload.error || `Impossible de récupérer l'année ${year}`);
                }
                const data = await response.json();
                priceValue.textContent = formatPrice(data.median_price_per_sqm);
            } catch (error) {
                console.error(error);
                priceValue.textContent = 'Donnée indisponible';
            }
        };

        yearSelect.addEventListener('change', (event) => {
            updatePrice(event.target.value);
        });

        updatePrice(yearSelect.value);
    }
})();
