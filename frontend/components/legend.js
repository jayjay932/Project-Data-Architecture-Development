/**
 * Composant Legend - Gestion de la légende de la carte
 */

class Legend {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.title = '';
        this.items = [];
    }

    /**
     * Met à jour la légende avec de nouvelles données
     * @param {string} title - Titre de la légende
     * @param {Array} items - Éléments de la légende [{color, label, value}]
     */
    update(title, items) {
        this.title = title;
        this.items = items;
        this.render();
    }

    /**
     * Génère la légende pour une métrique
     * @param {string} metric - Nom de la métrique
     * @param {Array} values - Valeurs de la métrique
     */
    generateFromMetric(metric, values) {
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min;
        const step = range / 4;

        const colors = [
            '#f1eef6',
            '#bdc9e1',
            '#74a9cf',
            '#2b8cbe',
            '#045a8d'
        ];

        const items = colors.map((color, index) => {
            const value = min + (step * index);
            return {
                color: color,
                label: this.formatValue(value, metric),
                value: value
            };
        });

        this.update(this.getMetricLabel(metric), items);
    }

    /**
     * Rend la légende dans le DOM
     */
    render() {
        if (!this.container) return;

        const html = `
            <h4>${this.title}</h4>
            <div class="legend-scale">
                ${this.items.map(item => `
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${item.color}"></div>
                        <span>${item.label}</span>
                    </div>
                `).join('')}
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Formate une valeur selon la métrique
     * @param {number} value - Valeur à formater
     * @param {string} metric - Type de métrique
     * @returns {string} Valeur formatée
     */
    formatValue(value, metric) {
        if (metric.includes('prix_m2')) {
            return `${Math.round(value).toLocaleString('fr-FR')} €/m²`;
        } else if (metric.includes('prix')) {
            return `${Math.round(value).toLocaleString('fr-FR')} €`;
        } else if (metric.includes('pct')) {
            return `${value.toFixed(1)}%`;
        } else {
            return Math.round(value).toLocaleString('fr-FR');
        }
    }

    /**
     * Retourne le label d'une métrique
     * @param {string} metric - Nom de la métrique
     * @returns {string} Label formaté
     */
    getMetricLabel(metric) {
        const labels = {
            'prix_m2_median_2024': 'Prix/m² médian 2024',
            'prix_median_2024': 'Prix médian 2024',
            'evolution_prix_2020_2024_pct': 'Évolution 2020-2024',
            'nb_stations_metro': 'Stations de métro',
            'trafic_total_metro': 'Trafic métro',
            'no2_moyen': 'NO2 moyen (µg/m³)',
            'pm10_moyen': 'PM10 moyen (µg/m³)',
            'o3_moyen': 'O3 moyen (µg/m³)'
        };
        
        return labels[metric] || metric;
    }

    /**
     * Masque la légende
     */
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }

    /**
     * Affiche la légende
     */
    show() {
        if (this.container) {
            this.container.style.display = 'block';
        }
    }

    /**
     * Nettoie la légende
     */
    clear() {
        this.title = '';
        this.items = [];
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Legend;
}
