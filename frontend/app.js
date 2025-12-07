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
    const metricsCache = new Map();
    const typologyCache = new Map();
    const surfaceCache = new Map();
    const priceHistoryCache = new Map();
    const TYPOLOGY_SEGMENTS = [
        { id: 'studio_t1', label: 'Studios / T1' },
        { id: 't2', label: 'T2' },
        { id: 't3', label: 'T3' },
        { id: 't4', label: 'T4' },
        { id: 't5_plus', label: 'T5 et +' }
    ];
    const TYPOLOGY_COLOR_MAP = {
        studio_t1: '#5DA5DA',
        t2: '#FAA43A',
        t3: '#60BD68',
        t4: '#B276B2',
        t5_plus: '#F17CB0'
    };
    const TYPOLOGY_FALLBACK_COLORS = ['#5DA5DA', '#FAA43A', '#60BD68', '#B276B2', '#F17CB0'];
    const SURFACE_GROUPS = [
        { id: 'lt_20', label: '< 20 m²' },
        { id: 'bt_20_40', label: '20 - 40 m²' },
        { id: 'bt_40_60', label: '40 - 60 m²' },
        { id: 'bt_60_80', label: '60 - 80 m²' },
        { id: 'bt_80_120', label: '80 - 120 m²' },
        { id: 'gt_120', label: '> 120 m²' }
    ];
    const SURFACE_COLOR_MAP = {
        lt_20: '#2563EB',
        bt_20_40: '#0EA5E9',
        bt_40_60: '#14B8A6',
        bt_60_80: '#F59E0B',
        bt_80_120: '#F97316',
        gt_120: '#DB2777'
    };
    const surfaceChartState = {
        canvas: null,
        tooltip: null,
        wrapper: null,
        bars: [],
        lastPayload: null
    };
    const comparisonState = {
        year: null,
        arrA: null,
        arrB: null,
        valid: false,
        dataA: null,
        dataB: null
    };
    const RADAR_FIELDS = [
        { key: 'prix_m2_median', label: 'Prix/m²', formatter: formatCurrency },
        { key: 'tx_logement_sociaux', label: 'Log. sociaux', formatter: formatPercent },
        { key: 'revenu_median', label: 'Revenu médian', formatter: formatCurrency },
        { key: 'densite_population', label: 'Densité', formatter: formatDensity },
        { key: 'transactions_total', label: 'Transactions', formatter: formatCompactNumber }
    ];
    const comparisonRadarState = {
        canvas: null,
        tooltip: null,
        wrapper: null,
        points: []
    };
    const priceTrendState = {
        canvas: null,
        tooltip: null,
        wrapper: null,
        points: [],
        lastPayload: null
    };
    const COMPARISON_FIELD_CONFIG = [
        { suffix: 'price', key: 'prix_m2_median', formatter: formatCurrency },
        {
            suffix: 'variation',
            key: 'variation',
            formatter: (value, data) => formatVariationDisplay(value, data.year)
        },
        { suffix: 'social', key: 'tx_logement_sociaux', formatter: formatPercent },
        { suffix: 'income', key: 'revenu_median', formatter: formatCurrency },
        { suffix: 'density', key: 'densite_population', formatter: formatDensity },
        {
            suffix: 'air',
            key: 'air_quality_global',
            formatter: (value) => value || 'N/A'
        }
    ];
    const typologyChartState = {
        canvas: null,
        tooltip: null,
        wrapper: null,
        arcs: [],
        centerX: 0,
        centerY: 0,
        radius: 0
    };

    document.addEventListener('DOMContentLoaded', () => {
        initializeMap();
        initializePriceTrendChart();
        initializeDashboardFilters();
        initializeTypologyChartInteractions();
        initializeSurfaceChartInteractions();
        initializeComparisonCards();
        initializeComparisonRadar();
        window.addEventListener('resize', handleSurfaceResize);
        window.addEventListener('resize', handlePriceTrendResize);
    });

    function initializeMap() {
        const mapElement = document.getElementById('map');
        const mapPopup = document.getElementById('map-popup');

        if (!mapElement || !mapPopup) {
            console.warn('Le conteneur de carte ou le popup est introuvable.');
            return;
        }

        const map = new maplibregl.Map({
            container: 'map',
            style: 'https://tiles.openfreemap.org/styles/bright',
            center: [2.3522, 48.8566],
            zoom: 11
        });

        map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

        let hoveredId = null;
        let lastHoveredCode = null;
        let activePopupCode = null;
        let infoRequestCounter = 0;
        let lastPopupPosition = null;
        const yearSelect = document.getElementById('year-select');

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
                        const arrondissementCode = formatArrondissementCode(props?.c_arinsee);
                        if (!arrondissementCode || !yearSelect) {
                            return;
                        }

                        if (arrondissementCode !== lastHoveredCode) {
                            lastHoveredCode = arrondissementCode;
                            activePopupCode = arrondissementCode;
                            void updateMapPopupWithMetrics({
                                arrondissementCode,
                                year: yearSelect.value,
                                point: e.point
                            });
                        } else {
                            positionPopup(e.point);
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
                        lastHoveredCode = null;
                        activePopupCode = null;
                        infoRequestCounter += 1;
                        hidePopup();

                        map.getCanvas().style.cursor = '';
                    });

                    map.on('click', 'arrondissements-fill', (e) => {
                        if (!e.features || !e.features.length || !yearSelect) {
                            return;
                        }

                        const props = e.features[0].properties;
                        const arrondissementCode = formatArrondissementCode(props?.c_arinsee);
                        if (!arrondissementCode) {
                            return;
                        }

                        lastHoveredCode = arrondissementCode;
                        activePopupCode = arrondissementCode;
                        void updateMapPopupWithMetrics({
                            arrondissementCode,
                            year: yearSelect.value,
                            point: e.point
                        });
                    });
                })
                .catch((error) => {
                    console.error(error);
                });
        });

        if (yearSelect) {
            yearSelect.addEventListener('change', () => {
                if (activePopupCode) {
                    void updateMapPopupWithMetrics({
                        arrondissementCode: activePopupCode,
                        year: yearSelect.value,
                        point: lastPopupPosition
                    });
                }
            });
        }

        function positionPopup(point) {
            if (!mapPopup || !point) {
                return;
            }

            const mapWidth = mapElement.clientWidth;
            const mapHeight = mapElement.clientHeight;
            const popupWidth = mapPopup.offsetWidth || 0;
            const popupHeight = mapPopup.offsetHeight || 0;
            const margin = 10;
            const pointerOffset = 12;

            let desiredLeft = point.x - popupWidth / 2;
            let desiredTop = point.y - popupHeight - pointerOffset;

            if (desiredTop < margin) {
                desiredTop = point.y + pointerOffset;
            }

            if (desiredTop + popupHeight > mapHeight - margin) {
                desiredTop = Math.max(margin, mapHeight - popupHeight - margin);
            }

            if (desiredLeft < margin) {
                desiredLeft = margin;
            }

            if (desiredLeft + popupWidth > mapWidth - margin) {
                desiredLeft = Math.max(margin, mapWidth - popupWidth - margin);
            }

            mapPopup.style.left = `${desiredLeft}px`;
            mapPopup.style.top = `${desiredTop}px`;
            lastPopupPosition = clonePoint(point);
        }

        function showPopup(content, point) {
            if (!mapPopup) {
                return;
            }

            mapPopup.innerHTML = content;
            mapPopup.style.display = 'block';
            mapPopup.style.visibility = 'hidden';

            if (point) {
                positionPopup(point);
            } else if (lastPopupPosition) {
                positionPopup(lastPopupPosition);
            }

            mapPopup.style.visibility = 'visible';
        }

        function hidePopup() {
            if (!mapPopup) {
                return;
            }
            mapPopup.style.display = 'none';
            mapPopup.style.visibility = 'hidden';
            mapPopup.innerHTML = '';
            lastPopupPosition = null;
        }

        function clonePoint(point) {
            if (!point) {
                return null;
            }
            return { x: point.x, y: point.y };
        }

        async function updateMapPopupWithMetrics({ arrondissementCode, year, point }) {
            if (!arrondissementCode || !year) {
                return;
            }

            const pointer = point ? clonePoint(point) : lastPopupPosition;
            const requestId = ++infoRequestCounter;
            showPopup(
                `
                    <h4>Chargement...</h4>
                    <p>Arrondissement ${arrondissementCode}</p>
                `,
                pointer
            );

            try {
                const metrics = await fetchMetrics(year, arrondissementCode);
                if (requestId !== infoRequestCounter) {
                    return;
                }
                showPopup(buildMetricsInfoPanel(metrics), pointer);
            } catch (error) {
                console.error(error);
                if (requestId === infoRequestCounter) {
                    showPopup(
                        `
                            <h4>Arrondissement ${arrondissementCode}</h4>
                            <p>Données indisponibles pour ${year}.</p>
                        `,
                        pointer
                    );
                }
            }
        }

        function formatArrondissementCode(raw) {
            if (raw === undefined || raw === null) {
                return null;
            }
            return String(raw).padStart(5, '0');
        }

        function buildMetricsInfoPanel(metrics) {
            return `
                <h4>${metrics.label || 'Arrondissement'}</h4>
                <ul class="map-info-list">
                    <li><strong>Année :</strong> ${metrics.year}</li>
                    <li><strong>Prix/m² médian :</strong> ${formatCurrency(metrics.prix_m2_median)}</li>
                    <li><strong>Taux logements sociaux :</strong> ${formatPercent(metrics.tx_logement_sociaux)}</li>
                    <li><strong>Revenu médian :</strong> ${formatCurrency(metrics.revenu_median)}</li>
                    <li><strong>Densité population :</strong> ${formatDensity(metrics.densite_population)}</li>
                    <li><strong>Qualité de l'air :</strong> ${metrics.air_quality_global || 'N/A'}</li>
                </ul>
            `;
        }
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

        const refreshDashboardData = () => {
            loadMetrics(state.year, state.arrondissement);
            loadTypology(state.year, state.arrondissement);
            loadSurfaceDistribution(state.year, state.arrondissement);
            loadPriceTrendHistory(state.arrondissement);
        };

        yearSelect.addEventListener('change', (event) => {
            state.year = event.target.value;
            refreshDashboardData();
        });

        arrondissementSelect.addEventListener('change', (event) => {
            state.arrondissement = event.target.value || 'all';
            refreshDashboardData();
        });

        refreshDashboardData();
    }

    async function loadMetrics(year, arrondissement) {
        setMetricsLoading();
        try {
            const data = await fetchMetrics(year, arrondissement);
            renderMetrics(data);
        } catch (error) {
            console.error(error);
            renderMetricsError();
        }
    }

    async function loadTypology(year, arrondissement) {
        setTypologyLoading('Chargement...');
        try {
            const data = await fetchTypology(year, arrondissement);
            renderTypologyChart(data);
        } catch (error) {
            console.error(error);
            renderTypologyError('Donnée indisponible');
        }
    }

    async function loadSurfaceDistribution(year, arrondissement) {
        setSurfaceLoading('Chargement...');
        try {
            const data = await fetchSurfaceDistribution(year, arrondissement);
            renderSurfaceChart(data);
        } catch (error) {
            console.error(error);
            renderSurfaceError('Donnée indisponible');
        }
    }

    async function loadPriceTrendHistory(arrondissement) {
        if (!priceTrendState.canvas) {
            return;
        }
        setPriceTrendLoading('Chargement...');
        try {
            const data = await fetchPriceHistory(arrondissement);
            renderPriceTrendChart(data);
        } catch (error) {
            console.error(error);
            renderPriceTrendError('Donnée indisponible');
        }
    }

    function initializeTypologyChartInteractions() {
        const canvas = document.getElementById('typology-chart');
        const tooltip = document.getElementById('typology-tooltip');
        if (!canvas || !tooltip) {
            return;
        }

        typologyChartState.canvas = canvas;
        typologyChartState.tooltip = tooltip;
        typologyChartState.wrapper = canvas.parentElement;

        canvas.addEventListener('mousemove', handleTypologyHover);
        canvas.addEventListener('mouseleave', hideTypologyTooltip);
    }

    function initializeSurfaceChartInteractions() {
        const canvas = document.getElementById('surface-chart');
        const tooltip = document.getElementById('surface-tooltip');
        if (!canvas || !tooltip) {
            return;
        }
        surfaceChartState.canvas = canvas;
        surfaceChartState.tooltip = tooltip;
        surfaceChartState.wrapper = canvas.parentElement;
        syncSurfaceCanvasSize();

        canvas.addEventListener('mousemove', handleSurfaceHover);
        canvas.addEventListener('mouseleave', hideSurfaceTooltip);
    }

    function initializePriceTrendChart() {
        const canvas = document.getElementById('price-trend-chart');
        const tooltip = document.getElementById('price-trend-tooltip');
        if (!canvas || !tooltip) {
            return;
        }
        priceTrendState.canvas = canvas;
        priceTrendState.tooltip = tooltip;
        priceTrendState.wrapper = canvas.parentElement;
        syncPriceTrendCanvasSize();
        canvas.addEventListener('mousemove', handlePriceTrendHover);
        canvas.addEventListener('mouseleave', hidePriceTrendTooltip);
    }

    function initializeComparisonRadar() {
        const canvas = document.getElementById('comparison-radar-chart');
        const tooltip = document.getElementById('comparison-radar-tooltip');
        if (!canvas || !tooltip) {
            return;
        }
        comparisonRadarState.canvas = canvas;
        comparisonRadarState.tooltip = tooltip;
        comparisonRadarState.wrapper = canvas.parentElement;
        setComparisonRadarLoading('Sélection en attente...');
        canvas.addEventListener('mousemove', handleComparisonRadarHover);
        canvas.addEventListener('mouseleave', hideComparisonRadarTooltip);
    }

    function initializeComparisonCards() {
        const yearSelect = document.getElementById('comparison-year-select');
        const arrSelectA = document.getElementById('comparison-arrA-select');
        const arrSelectB = document.getElementById('comparison-arrB-select');
        if (!yearSelect || !arrSelectA || !arrSelectB) {
            return;
        }

        const overviewYearSelect = document.getElementById('year-select');
        if (overviewYearSelect && !yearSelect.options.length) {
            yearSelect.innerHTML = overviewYearSelect.innerHTML;
            yearSelect.value = overviewYearSelect.value;
        }
        if (!yearSelect.options.length) {
            ['2020', '2021', '2022', '2023', '2024', '2025'].forEach((year, index) => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (index === 0) {
                    option.selected = true;
                }
                yearSelect.appendChild(option);
            });
        }

        const arrondissementSelect = document.getElementById('arrondissement-select');
        const populateArrSelect = (targetSelect) => {
            if (!targetSelect) {
                return;
            }
            if (arrondissementSelect) {
                const options = Array.from(arrondissementSelect.options)
                    .filter((option) => option.value && option.value !== 'all');
                targetSelect.innerHTML = options
                    .map((option) => `<option value="${option.value}">${option.textContent}</option>`)
                    .join('');
            }
        };
        if (!arrSelectA.options.length) {
            populateArrSelect(arrSelectA);
        }
        if (!arrSelectB.options.length) {
            populateArrSelect(arrSelectB);
            if (arrSelectB.options.length > 1) {
                arrSelectB.selectedIndex = 1;
            }
        }

        const state = {
            year: yearSelect.value,
            arrA: arrSelectA.value,
            arrB: arrSelectB.value,
            valid: false
        };
        comparisonState.year = state.year;
        comparisonState.arrA = state.arrA;
        comparisonState.arrB = state.arrB;

        const refreshComparison = () => {
            const errorElement = document.getElementById('comparison-arrB-error');
            const invalid = state.arrA === state.arrB;
            state.valid = !invalid;
            if (errorElement) {
                errorElement.textContent = invalid ? 'Veuillez choisir deux arrondissements différents.' : '';
            }

            if (!state.valid) {
                comparisonState.valid = false;
                comparisonState.dataA = null;
                comparisonState.dataB = null;
                renderComparisonCardInvalid('a');
                renderComparisonCardInvalid('b');
                renderComparisonRadar();
                return;
            }

            comparisonState.valid = true;
            comparisonState.year = state.year;
            comparisonState.arrA = state.arrA;
            comparisonState.arrB = state.arrB;
            loadComparisonCard('a', state.year, state.arrA);
            loadComparisonCard('b', state.year, state.arrB);
        };

        yearSelect.addEventListener('change', (event) => {
            state.year = event.target.value;
            comparisonState.year = state.year;
            refreshComparison();
        });
        arrSelectA.addEventListener('change', (event) => {
            state.arrA = event.target.value;
            comparisonState.arrA = state.arrA;
            refreshComparison();
        });
        arrSelectB.addEventListener('change', (event) => {
            state.arrB = event.target.value;
            comparisonState.arrB = state.arrB;
            refreshComparison();
        });

        refreshComparison();
    }

    function syncSurfaceCanvasSize() {
        const { canvas, wrapper } = surfaceChartState;
        if (!canvas || !wrapper) {
            return;
        }
        const width = Math.floor(wrapper.clientWidth || canvas.width);
        const height = Math.floor(wrapper.clientHeight || canvas.height);
        if (width && canvas.width !== width) {
            canvas.width = width;
        }
        if (height && canvas.height !== height) {
            canvas.height = height;
        }
    }

    function handleSurfaceResize() {
        if (!surfaceChartState.canvas) {
            return;
        }
        syncSurfaceCanvasSize();
        if (surfaceChartState.lastPayload) {
            renderSurfaceChart(surfaceChartState.lastPayload);
        }
    }

    function syncPriceTrendCanvasSize() {
        const { canvas, wrapper } = priceTrendState;
        if (!canvas || !wrapper) {
            return;
        }
        const width = Math.floor(wrapper.clientWidth || canvas.width);
        const height = Math.floor(wrapper.clientHeight || canvas.height);
        if (width && canvas.width !== width) {
            canvas.width = width;
        }
        if (height && canvas.height !== height) {
            canvas.height = height;
        }
    }

    function handlePriceTrendResize() {
        if (!priceTrendState.canvas) {
            return;
        }
        syncPriceTrendCanvasSize();
        if (priceTrendState.lastPayload) {
            renderPriceTrendChart(priceTrendState.lastPayload);
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

    function setTypologyLoading(message) {
        const loadingElement = document.getElementById('typology-loading');
        const canvas = document.getElementById('typology-chart');
        const legend = document.getElementById('typology-legend');
        hideTypologyTooltip();
        typologyChartState.arcs = [];
        typologyChartState.centerX = 0;
        typologyChartState.centerY = 0;
        typologyChartState.radius = 0;
        if (legend) {
            legend.innerHTML = '';
        }
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            loadingElement.textContent = message;
        }
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        if (legend) {
            legend.innerHTML = '';
        }
    }

    function renderTypologyError(message) {
        setTypologyLoading(message);
    }

    function renderTypologyChart(data) {
        const canvas = document.getElementById('typology-chart');
        const legend = document.getElementById('typology-legend');
        const loadingElement = document.getElementById('typology-loading');

        if (!canvas) {
            return;
        }

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hideTypologyTooltip();
        if (legend) {
            legend.innerHTML = '';
        }
        typologyChartState.canvas = typologyChartState.canvas || canvas;
        typologyChartState.wrapper = typologyChartState.wrapper || canvas.parentElement;
        typologyChartState.tooltip = typologyChartState.tooltip || document.getElementById('typology-tooltip');

        const apiSegments = Array.isArray(data?.segments) ? data.segments : [];
        const normalizedSegments = TYPOLOGY_SEGMENTS.map((segmentMeta) => {
            const match = apiSegments.find((segment) => segment.id === segmentMeta.id) || {};
            return {
                id: segmentMeta.id,
                label: segmentMeta.label,
                value: typeof match.value === 'number' ? match.value : 0,
                count: typeof match.count === 'number' ? match.count : 0
            };
        });

        const drawableSegments = normalizedSegments.filter((segment) => segment.value > 0);
        const totalValue = drawableSegments.reduce((sum, segment) => sum + segment.value, 0);

        if (!totalValue) {
            renderTypologyError('Aucune donnée pour cette sélection');
            return;
        }

        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 12;
        let currentAngle = -Math.PI / 2;

        typologyChartState.centerX = centerX;
        typologyChartState.centerY = centerY;
        typologyChartState.radius = radius;
        typologyChartState.arcs = [];

        drawableSegments.forEach((segment, index) => {
            const color = TYPOLOGY_COLOR_MAP[segment.id] || TYPOLOGY_FALLBACK_COLORS[index % TYPOLOGY_FALLBACK_COLORS.length];
            const sliceAngle = (segment.value / totalValue) * Math.PI * 2;
            const startAngle = currentAngle;
            const endAngle = currentAngle + sliceAngle;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = color;
            ctx.fill();

            const midAngle = startAngle + sliceAngle / 2;
            const canDrawInside = segment.value >= 12;
            if (canDrawInside) {
                drawInnerLabel(ctx, segment, color, centerX, centerY, radius, midAngle);
            }

            typologyChartState.arcs.push({
                id: segment.id,
                label: segment.label,
                value: segment.value,
                count: segment.count,
                color,
                startAngle: normalizeAngle(startAngle),
                endAngle: normalizeAngle(endAngle)
            });

            currentAngle = endAngle;
        });

        if (legend) {
            normalizedSegments.forEach((segment, index) => {
                const color = TYPOLOGY_COLOR_MAP[segment.id] || TYPOLOGY_FALLBACK_COLORS[index % TYPOLOGY_FALLBACK_COLORS.length];
                const item = document.createElement('li');
                item.innerHTML = `
                    <span class="legend-color" style="background: ${color};"></span>
                    ${segment.label}
                `;
                legend.appendChild(item);
            });
        }
    }

    function setSurfaceLoading(message) {
        const loadingElement = document.getElementById('surface-loading');
        const canvas = document.getElementById('surface-chart');
        hideSurfaceTooltip();
        surfaceChartState.bars = [];
        syncSurfaceCanvasSize();
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            loadingElement.textContent = message;
        }
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    function renderSurfaceError(message) {
        setSurfaceLoading(message);
    }

    function renderSurfaceChart(data) {
        const canvas = document.getElementById('surface-chart');
        const loadingElement = document.getElementById('surface-loading');
        if (!canvas) {
            return;
        }

        const ctx = canvas.getContext('2d');
        surfaceChartState.lastPayload = data;
        syncSurfaceCanvasSize();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hideSurfaceTooltip();
        surfaceChartState.canvas = surfaceChartState.canvas || canvas;
        surfaceChartState.wrapper = surfaceChartState.wrapper || canvas.parentElement;
        surfaceChartState.tooltip = surfaceChartState.tooltip || document.getElementById('surface-tooltip');

        const apiSegments = Array.isArray(data?.segments) ? data.segments : [];
        const normalizedSegments = SURFACE_GROUPS.map((segmentMeta, index) => {
            const match = apiSegments.find((segment) => segment.id === segmentMeta.id) || {};
            return {
                id: segmentMeta.id,
                label: segmentMeta.label,
                value: typeof match.value === 'number' ? match.value : 0,
                count: typeof match.count === 'number' ? match.count : 0,
                color: SURFACE_COLOR_MAP[segmentMeta.id] || Object.values(SURFACE_COLOR_MAP)[index] || '#2563EB'
            };
        });

        const totalValue = normalizedSegments.reduce((sum, segment) => sum + segment.value, 0);
        if (!totalValue) {
            renderSurfaceError('Aucune donnée pour cette sélection');
            return;
        }

        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        ctx.font = '600 13px "Inter", sans-serif';
        const longestLabel = normalizedSegments.reduce((max, segment) => {
            return Math.max(max, ctx.measureText(segment.label).width);
        }, 0);
        const dynamicPaddingLeft = Math.min(160, Math.max(80, longestLabel + 26));
        const padding = { top: 28, right: 18, bottom: 20, left: dynamicPaddingLeft };
        const chartWidth = canvas.width - padding.left - padding.right;
        const barHeight = 22;
        const barGap = 8;
        const chartHeight = normalizedSegments.length * (barHeight + barGap) - barGap;
        surfaceChartState.bars = [];
        const maxSegmentValue = Math.max(...normalizedSegments.map((segment) => segment.value), 1);

        normalizedSegments.forEach((segment, index) => {
            const barY = padding.top + index * (barHeight + barGap);
            const barWidth = Math.max((segment.value / maxSegmentValue) * chartWidth, 0);
            ctx.fillStyle = segment.color;
            ctx.fillRect(padding.left, barY, barWidth, barHeight);

            ctx.fillStyle = '#1F2933';
            ctx.font = '600 13px "Inter", sans-serif';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            ctx.fillText(segment.label, padding.left - 14, barY + barHeight / 2);

            const percentText = `${segment.value.toFixed(1)}%`;
            const drawInside = barWidth > 48;
            ctx.font = '600 12px "Inter", sans-serif';
            ctx.textAlign = drawInside ? 'right' : 'left';
            ctx.fillStyle = drawInside ? '#FFFFFF' : '#0F172A';
            const percentX = drawInside ? padding.left + barWidth - 10 : padding.left + barWidth + 10;
            ctx.fillText(percentText, Math.min(percentX, padding.left + chartWidth - 4), barY + barHeight / 2);

            surfaceChartState.bars.push({
                x: padding.left,
                y: barY,
                width: Math.max(barWidth, 1),
                height: barHeight,
                maxWidth: chartWidth,
                segment
            });
        });
    }

    function setPriceTrendLoading(message) {
        const loadingElement = document.getElementById('price-trend-loading');
        const canvas = document.getElementById('price-trend-chart');
        hidePriceTrendTooltip();
        priceTrendState.points = [];
        syncPriceTrendCanvasSize();
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            loadingElement.textContent = message;
        }
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    function renderPriceTrendError(message) {
        setPriceTrendLoading(message);
    }

    function renderPriceTrendChart(data) {
        const canvas = document.getElementById('price-trend-chart');
        const loadingElement = document.getElementById('price-trend-loading');
        if (!canvas) {
            return;
        }

        const ctx = canvas.getContext('2d');
        priceTrendState.lastPayload = data;
        syncPriceTrendCanvasSize();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hidePriceTrendTooltip();
        priceTrendState.canvas = priceTrendState.canvas || canvas;
        priceTrendState.wrapper = priceTrendState.wrapper || canvas.parentElement;
        priceTrendState.tooltip = priceTrendState.tooltip || document.getElementById('price-trend-tooltip');

        const priceSeries = Array.isArray(data?.prices) ? data.prices : [];
        const validPoints = priceSeries
            .map((point) => ({
                year: point.year,
                value: typeof point.median_price_per_sqm === 'number' ? point.median_price_per_sqm : null
            }))
            .filter((point) => point.year && point.value !== null)
            .sort((a, b) => a.year - b.year);

        if (!validPoints.length) {
            renderPriceTrendError('Aucune donnée pour cette sélection');
            return;
        }

        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        const padding = { top: 20, right: 20, bottom: 36, left: 48 };
        const chartWidth = canvas.width - padding.left - padding.right;
        const chartHeight = canvas.height - padding.top - padding.bottom;
        const values = validPoints.map((point) => point.value);
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const range = maxValue - minValue || 1;

        const getX = (index) => {
            if (validPoints.length === 1) {
                return padding.left + chartWidth / 2;
            }
            return padding.left + (index / (validPoints.length - 1)) * chartWidth;
        };
        const getY = (value) =>
            padding.top + (1 - (value - minValue) / range) * chartHeight;

        ctx.strokeStyle = '#E5E7EB';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top + chartHeight);
        ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
        ctx.stroke();

        ctx.lineWidth = 3;
        ctx.strokeStyle = '#2563EB';
        ctx.beginPath();
        validPoints.forEach((point, index) => {
            const x = getX(index);
            const y = getY(point.value);
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();

        ctx.fillStyle = 'rgba(37, 99, 235, 0.15)';
        ctx.beginPath();
        validPoints.forEach((point, index) => {
            const x = getX(index);
            const y = getY(point.value);
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
        ctx.lineTo(padding.left, padding.top + chartHeight);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#1F2933';
        ctx.font = '600 12px "Inter", sans-serif';
        validPoints.forEach((point, index) => {
            const x = getX(index);
            const y = getY(point.value);
            ctx.beginPath();
            ctx.fillStyle = '#FFFFFF';
            ctx.arc(x, y, 5.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.fillStyle = '#2563EB';
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();

            const label = formatCurrency(point.value);
            const labelWidth = ctx.measureText(label).width;
            const spaceTop = y - padding.top;
            const spaceBottom = padding.top + chartHeight - y;
            const placeAbove = spaceTop >= 28 || spaceTop >= spaceBottom;
            ctx.textBaseline = placeAbove ? 'bottom' : 'top';
            let labelY = placeAbove ? Math.max(y - 10, padding.top + 4) : Math.min(y + 10, padding.top + chartHeight - 4);
            let labelX = x;
            const minX = padding.left + labelWidth / 2 + 4;
            const maxX = padding.left + chartWidth - labelWidth / 2 - 4;
            if (labelX < minX) {
                labelX = minX;
            } else if (labelX > maxX) {
                labelX = maxX;
            }
            ctx.textAlign = 'center';
            ctx.fillStyle = '#0F172A';
            ctx.fillText(label, labelX, labelY);
        });

        ctx.fillStyle = '#6B7280';
        ctx.textAlign = 'center';
        validPoints.forEach((point, index) => {
            const x = getX(index);
            ctx.fillText(point.year, x, canvas.height - 8);
        });

        priceTrendState.points = validPoints.map((point, index) => {
            return {
                x: getX(index),
                y: getY(point.value),
                value: point.value,
                year: point.year
            };
        });
    }

    async function loadComparisonCard(side, year, arrondissement) {
        setComparisonCardLoading(side);
        try {
            const data = await fetchMetrics(year, arrondissement);
            renderComparisonCard(side, data);
        } catch (error) {
            console.error(error);
            renderComparisonCardError(side);
        }
    }

    function setComparisonCardLoading(side) {
        const lowerSide = side.toLowerCase();
        const nameElement = document.getElementById(`comparison-card-${lowerSide}-name`);
        if (nameElement) {
            nameElement.textContent = 'Chargement...';
        }
        COMPARISON_FIELD_CONFIG.forEach((field) => {
            const element = document.getElementById(`comparison-card-${lowerSide}-${field.suffix}`);
            if (element) {
                element.textContent = 'Chargement...';
            }
        });
    }

    function renderComparisonCard(side, data) {
        const lowerSide = side.toLowerCase();
        const nameElement = document.getElementById(`comparison-card-${lowerSide}-name`);
        if (nameElement) {
            const label = data.label || data.code_commune || 'Arrondissement';
            nameElement.textContent = `${label} (${data.year})`;
        }
        COMPARISON_FIELD_CONFIG.forEach((field) => {
            const element = document.getElementById(`comparison-card-${lowerSide}-${field.suffix}`);
            if (!element) {
                return;
            }
            const rawValue = data[field.key];
            const formatted =
                field.formatter && typeof field.formatter === 'function'
                    ? field.formatter(rawValue, data)
                    : rawValue ?? 'N/A';
            element.textContent = formatted ?? 'N/A';
        });
        comparisonState[`data${side.toUpperCase()}`] = data;
        renderComparisonRadar();
    }

    function renderComparisonCardError(side) {
        const lowerSide = side.toLowerCase();
        const nameElement = document.getElementById(`comparison-card-${lowerSide}-name`);
        if (nameElement) {
            nameElement.textContent = 'Donnée indisponible';
        }
        COMPARISON_FIELD_CONFIG.forEach((field) => {
            const element = document.getElementById(`comparison-card-${lowerSide}-${field.suffix}`);
            if (element) {
                element.textContent = 'N/A';
            }
        });
        comparisonState[`data${side.toUpperCase()}`] = null;
        renderComparisonRadar();
    }

    function renderComparisonCardInvalid(side) {
        const lowerSide = side.toLowerCase();
        const nameElement = document.getElementById(`comparison-card-${lowerSide}-name`);
        if (nameElement) {
            nameElement.textContent = 'Sélection invalide';
        }
        COMPARISON_FIELD_CONFIG.forEach((field) => {
            const element = document.getElementById(`comparison-card-${lowerSide}-${field.suffix}`);
            if (element) {
                element.textContent = 'N/A';
            }
        });
        comparisonState[`data${side.toUpperCase()}`] = null;
        renderComparisonRadar();
    }

    function setComparisonRadarLoading(message) {
        const loadingElement = document.getElementById('comparison-radar-loading');
        const canvas = document.getElementById('comparison-radar-chart');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            loadingElement.textContent = message;
        }
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        comparisonRadarState.points = [];
        hideComparisonRadarTooltip();
    }

    function renderComparisonRadarEmpty(message) {
        setComparisonRadarLoading(message || 'Sélection invalide');
    }

    function renderComparisonRadar() {
        const canvas = comparisonRadarState.canvas;
        if (!canvas) {
            return;
        }
        const loadingElement = document.getElementById('comparison-radar-loading');
        if (
            !comparisonState.valid ||
            !comparisonState.dataA ||
            !comparisonState.dataB
        ) {
            renderComparisonRadarEmpty(
                comparisonState.valid ? 'Données insuffisantes' : 'Sélection invalide'
            );
            return;
        }

        const ctx = canvas.getContext('2d');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hideComparisonRadarTooltip();

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 32;
        const angleStep = (Math.PI * 2) / RADAR_FIELDS.length;
        const axisInfos = RADAR_FIELDS.map((field) => {
            const valueA = toNumericValue(comparisonState.dataA[field.key]);
            const valueB = toNumericValue(comparisonState.dataB[field.key]);
            const maxValue = Math.max(
                1,
                valueA ?? 0,
                valueB ?? 0
            );
            return {
                field,
                valueA: valueA ?? 0,
                valueB: valueB ?? 0,
                maxValue
            };
        });

        ctx.strokeStyle = '#E5E7EB';
        ctx.lineWidth = 1;
        for (let level = 1; level <= 4; level += 1) {
            const levelRadius = (radius * level) / 4;
            ctx.beginPath();
            axisInfos.forEach((_, index) => {
                const angle = -Math.PI / 2 + index * angleStep;
                const x = centerX + Math.cos(angle) * levelRadius;
                const y = centerY + Math.sin(angle) * levelRadius;
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            ctx.closePath();
            ctx.stroke();
        }

        axisInfos.forEach((axis, index) => {
            const angle = -Math.PI / 2 + index * angleStep;
            const labelRadius = radius + 22;
            let x = centerX + Math.cos(angle) * labelRadius;
            let y = centerY + Math.sin(angle) * labelRadius;
            const labelWidth = ctx.measureText(axis.field.label).width;
            if (x + labelWidth / 2 > canvas.width) {
                x = canvas.width - labelWidth / 2 - 4;
            } else if (x - labelWidth / 2 < 0) {
                x = labelWidth / 2 + 4;
            }
            if (y < 12) {
                y = 12;
            } else if (y > canvas.height - 4) {
                y = canvas.height - 4;
            }
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
            ctx.stroke();

            ctx.save();
            ctx.fillStyle = '#1F2933';
            ctx.font = '600 12px "Inter", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(axis.field.label, x, y);
            ctx.restore();
        });

        const datasets = [
            {
                id: 'A',
                color: '#2563EB',
                fill: 'rgba(37, 99, 235, 0.2)',
                border: '#2563EB',
                data: axisInfos.map((axis) => ({
                    raw: axis.valueA,
                    normalized: axis.maxValue ? axis.valueA / axis.maxValue : 0,
                    formatted:
                        axis.field.formatter?.(axis.valueA) ??
                        (axis.valueA || axis.valueA === 0
                            ? axis.valueA.toString()
                            : 'N/A'),
                    label: axis.field.label
                })),
                label: comparisonState.dataA?.label || 'A'
            },
            {
                id: 'B',
                color: '#EC4899',
                fill: 'rgba(236, 72, 153, 0.2)',
                border: '#EC4899',
                data: axisInfos.map((axis) => ({
                    raw: axis.valueB,
                    normalized: axis.maxValue ? axis.valueB / axis.maxValue : 0,
                    formatted:
                        axis.field.formatter?.(axis.valueB) ??
                        (axis.valueB || axis.valueB === 0
                            ? axis.valueB.toString()
                            : 'N/A'),
                    label: axis.field.label
                })),
                label: comparisonState.dataB?.label || 'B'
            }
        ];

        comparisonRadarState.points = [];
        datasets.forEach((dataset) => {
            ctx.beginPath();
            dataset.data.forEach((pointData, index) => {
                const angle = -Math.PI / 2 + index * angleStep;
                const x =
                    centerX + Math.cos(angle) * radius * Math.max(pointData.normalized, 0);
                const y =
                    centerY + Math.sin(angle) * radius * Math.max(pointData.normalized, 0);
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
                comparisonRadarState.points.push({
                    x,
                    y,
                    dataset: dataset.label,
                    value: pointData.formatted,
                    label: pointData.label
                });
            });
            ctx.closePath();
            ctx.fillStyle = dataset.fill;
            ctx.strokeStyle = dataset.border;
            ctx.lineWidth = 2;
            ctx.fill();
            ctx.stroke();

            dataset.data.forEach((pointData, index) => {
                const angle = -Math.PI / 2 + index * angleStep;
                const x =
                    centerX + Math.cos(angle) * radius * Math.max(pointData.normalized, 0);
                const y =
                    centerY + Math.sin(angle) * radius * Math.max(pointData.normalized, 0);
                ctx.beginPath();
                ctx.fillStyle = '#FFFFFF';
                ctx.arc(x, y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.fillStyle = dataset.border;
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        });
    }

    function handleComparisonRadarHover(event) {
        const { canvas, tooltip, wrapper, points } = comparisonRadarState;
        if (!canvas || !tooltip || !wrapper || !points.length) {
            hideComparisonRadarTooltip();
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const hoveredPoint = points.find(
            (point) => Math.hypot(point.x - x, point.y - y) <= 10
        );
        if (!hoveredPoint) {
            hideComparisonRadarTooltip();
            return;
        }
        showComparisonRadarTooltip(hoveredPoint, event);
    }

    function showComparisonRadarTooltip(point, event) {
        const { tooltip, wrapper } = comparisonRadarState;
        if (!tooltip || !wrapper) {
            return;
        }
        tooltip.innerHTML = `
            <p><strong>${point.dataset}</strong></p>
            <p>${point.label}</p>
            <p>${point.value}</p>
        `;
        const rect = wrapper.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        tooltip.style.left = `${offsetX}px`;
        tooltip.style.top = `${offsetY}px`;
        tooltip.style.display = 'block';
    }

    function hideComparisonRadarTooltip() {
        if (comparisonRadarState.tooltip) {
            comparisonRadarState.tooltip.style.display = 'none';
        }
    }

    async function fetchMetrics(year, arrondissement) {
        const cacheKey = `${year}-${arrondissement}`;
        if (metricsCache.has(cacheKey)) {
            return metricsCache.get(cacheKey);
        }

        const url = new URL(`${API_BASE_URL}/api/metrics`);
        url.searchParams.set('year', year);
        url.searchParams.set('arrondissement', arrondissement);
        const response = await fetch(url);
        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.error || 'Réponse serveur invalide');
        }
        const data = await response.json();
        metricsCache.set(cacheKey, data);
        return data;
    }

    async function fetchTypology(year, arrondissement) {
        const cacheKey = `${year}-${arrondissement}`;
        if (typologyCache.has(cacheKey)) {
            return typologyCache.get(cacheKey);
        }

        const url = new URL(`${API_BASE_URL}/api/typology`);
        url.searchParams.set('year', year);
        url.searchParams.set('arrondissement', arrondissement);
        const response = await fetch(url);
        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.error || 'Réponse serveur invalide');
        }
        const data = await response.json();
        typologyCache.set(cacheKey, data);
        return data;
    }

    async function fetchSurfaceDistribution(year, arrondissement) {
        const cacheKey = `${year}-${arrondissement}`;
        if (surfaceCache.has(cacheKey)) {
            return surfaceCache.get(cacheKey);
        }

        const url = new URL(`${API_BASE_URL}/api/surfaces`);
        url.searchParams.set('year', year);
        url.searchParams.set('arrondissement', arrondissement);
        const response = await fetch(url);
        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.error || 'Réponse serveur invalide');
        }
        const data = await response.json();
        surfaceCache.set(cacheKey, data);
        return data;
    }

    async function fetchPriceHistory(arrondissement) {
        const cacheKey = arrondissement || 'all';
        if (priceHistoryCache.has(cacheKey)) {
            return priceHistoryCache.get(cacheKey);
        }
        const url = new URL(`${API_BASE_URL}/api/price/history`);
        url.searchParams.set('arrondissement', arrondissement || 'all');
        const response = await fetch(url);
        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.error || 'Réponse serveur invalide');
        }
        const data = await response.json();
        priceHistoryCache.set(cacheKey, data);
        return data;
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

    function formatVariationDisplay(value, year) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            return 'N/A';
        }
        const sign = value > 0 ? '+' : value < 0 ? '' : '';
        const symbol = value > 0 ? '↑' : value < 0 ? '↓' : '→';
        const referenceYear = typeof year === 'number' ? ` vs ${year - 1}` : '';
        return `${symbol} ${sign}${value.toFixed(2)}%${referenceYear}`;
    }

    function formatCompactNumber(value) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            return 'N/A';
        }
        return new Intl.NumberFormat('fr-FR', {
            notation: 'compact',
            maximumFractionDigits: 1
        }).format(value);
    }

    function toNumericValue(value) {
        if (typeof value === 'number' && Number.isFinite(value)) {
            return value;
        }
        return null;
    }

    function normalizeAngle(angle) {
        const twoPi = Math.PI * 2;
        let normalized = angle % twoPi;
        if (normalized < 0) {
            normalized += twoPi;
        }
        return normalized;
    }

    function isAngleWithinArc(angle, arc) {
        if (arc.startAngle <= arc.endAngle) {
            return angle >= arc.startAngle && angle < arc.endAngle;
        }
        return angle >= arc.startAngle || angle < arc.endAngle;
    }

    function handleTypologyHover(event) {
        const { canvas, tooltip, wrapper, arcs, centerX, centerY, radius } = typologyChartState;
        if (!canvas || !tooltip || !wrapper || !arcs.length) {
            hideTypologyTooltip();
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const dx = x - centerX;
        const dy = y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance > radius || distance < 10) {
            hideTypologyTooltip();
            return;
        }

        const angle = normalizeAngle(Math.atan2(dy, dx));
        const segment = arcs.find((arc) => isAngleWithinArc(angle, arc));
        if (!segment) {
            hideTypologyTooltip();
            return;
        }

        showTypologyTooltip(segment, event);
    }

    function showTypologyTooltip(segment, event) {
        const { tooltip, wrapper } = typologyChartState;
        if (!tooltip || !wrapper) {
            return;
        }
        tooltip.innerHTML = `
            <p><strong>${segment.label}</strong></p>
            <p>Part : ${segment.value.toFixed(1)}%</p>
            <p>Transactions : ${segment.count}</p>
        `;
        const rect = wrapper.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        tooltip.style.left = `${offsetX}px`;
        tooltip.style.top = `${offsetY}px`;
        tooltip.style.display = 'block';
    }

    function hideTypologyTooltip() {
        if (typologyChartState.tooltip) {
            typologyChartState.tooltip.style.display = 'none';
        }
    }

    function handleSurfaceHover(event) {
        const { canvas, tooltip, wrapper, bars } = surfaceChartState;
        if (!canvas || !tooltip || !wrapper || !bars.length) {
            hideSurfaceTooltip();
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const hoveredBar = bars.find(
            (bar) => x >= bar.x && x <= bar.x + bar.width && y >= bar.y && y <= bar.y + bar.height
        );
        if (!hoveredBar) {
            hideSurfaceTooltip();
            return;
        }

        showSurfaceTooltip(hoveredBar.segment, event);
    }

    function showSurfaceTooltip(segment, event) {
        const { tooltip, wrapper } = surfaceChartState;
        if (!tooltip || !wrapper) {
            return;
        }

        tooltip.innerHTML = `
            <p><strong>Surface : ${segment.label}</strong></p>
            <p>Part : ${segment.value.toFixed(1)}%</p>
            <p>Transactions : ${segment.count}</p>
        `;
        const rect = wrapper.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        tooltip.style.left = `${offsetX}px`;
        tooltip.style.top = `${offsetY}px`;
        tooltip.style.display = 'block';
    }

    function hideSurfaceTooltip() {
        if (surfaceChartState.tooltip) {
            surfaceChartState.tooltip.style.display = 'none';
        }
    }

    function handlePriceTrendHover(event) {
        const { canvas, tooltip, wrapper, points } = priceTrendState;
        if (!canvas || !tooltip || !wrapper || !points.length) {
            hidePriceTrendTooltip();
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const radius = 12;
        const hoveredPoint = points.find(
            (point) => Math.hypot(point.x - x, point.y - y) <= radius
        );
        if (!hoveredPoint) {
            hidePriceTrendTooltip();
            return;
        }
        showPriceTrendTooltip(hoveredPoint, event);
    }

    function showPriceTrendTooltip(point, event) {
        const { tooltip, wrapper } = priceTrendState;
        if (!tooltip || !wrapper) {
            return;
        }
        tooltip.innerHTML = `
            <p><strong>${point.year}</strong></p>
            <p>Prix médian : ${formatCurrency(point.value)}</p>
        `;
        const rect = wrapper.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        tooltip.style.left = `${offsetX}px`;
        tooltip.style.top = `${offsetY}px`;
        tooltip.style.display = 'block';
    }

    function hidePriceTrendTooltip() {
        if (priceTrendState.tooltip) {
            priceTrendState.tooltip.style.display = 'none';
        }
    }

    function drawInnerLabel(ctx, segment, color, centerX, centerY, radius, angle) {
        const label = segment.label;
        const percent = `${segment.value.toFixed(1)}%`;
        const textRadius = radius * 0.55;
        const textX = centerX + Math.cos(angle) * textRadius;
        const textY = centerY + Math.sin(angle) * textRadius;

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const labelFont = 'bold 13px "Inter", sans-serif';
        const percentFont = '600 12px "Inter", sans-serif';
        ctx.font = labelFont;
        const labelWidth = ctx.measureText(label).width;
        ctx.font = percentFont;
        const percentWidth = ctx.measureText(percent).width;
        const boxWidth = Math.max(labelWidth, percentWidth) + 28;
        const boxHeight = 38;

        drawRoundedRect(ctx, textX - boxWidth / 2, textY - boxHeight / 2, boxWidth, boxHeight, 12, 'rgba(255,255,255,0.94)', `rgba(0,0,0,0.12)`);
        ctx.fillStyle = '#1f2933';
        ctx.font = labelFont;
        ctx.fillText(label, textX, textY - 8);
        ctx.font = percentFont;
        ctx.fillText(percent, textX, textY + 8);
        ctx.restore();
    }

    function drawOuterLabel(ctx, segment, color, centerX, centerY, radius, angle) {
        const percent = `${segment.value.toFixed(1)}%`;
        const label = segment.label;
        const lineStartX = centerX + Math.cos(angle) * radius;
        const lineStartY = centerY + Math.sin(angle) * radius;
        const lineMidX = centerX + Math.cos(angle) * (radius + 16);
        const lineMidY = centerY + Math.sin(angle) * (radius + 16);
        const horizontalX = lineMidX + (Math.cos(angle) >= 0 ? 18 : -18);

        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(lineStartX, lineStartY);
        ctx.lineTo(lineMidX, lineMidY);
        ctx.lineTo(horizontalX, lineMidY);
        ctx.stroke();

        const textAlignRight = Math.cos(angle) < 0;
        const boxWidth = Math.max(
            ctx.measureText(label).width,
            ctx.measureText(percent).width
        ) + 20;
        const boxHeight = 34;
        const boxX = textAlignRight ? horizontalX - boxWidth - 6 : horizontalX + 6;
        const boxY = lineMidY - boxHeight / 2;
        drawRoundedRect(ctx, boxX, boxY, boxWidth, boxHeight, 10, 'rgba(255,255,255,0.97)', color);

        ctx.fillStyle = '#1f2933';
        ctx.textAlign = textAlignRight ? 'right' : 'left';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 13px \"Inter\", sans-serif';
        const textX = textAlignRight ? boxX + boxWidth - 10 : boxX + 10;
        ctx.fillText(label, textX, boxY + 12);

        ctx.font = '600 12px \"Inter\", sans-serif';
        ctx.fillText(percent, textX, boxY + boxHeight - 12);
        ctx.restore();
    }

    function drawRoundedRect(ctx, x, y, width, height, radius, fillStyle, strokeStyle) {
        const r = Math.min(radius, width / 2, height / 2);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + width - r, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + r);
        ctx.lineTo(x + width, y + height - r);
        ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
        ctx.lineTo(x + r, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        if (fillStyle) {
            ctx.fillStyle = fillStyle;
            ctx.fill();
        }
        if (strokeStyle) {
            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    }
})();
