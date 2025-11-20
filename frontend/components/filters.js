/**
 * Composant Filters - Gestion des filtres du dashboard
 */

class Filters {
    constructor() {
        this.currentMetric = 'prix_m2_median_2024';
        this.currentYear = 2024;
        this.listeners = [];
        this.initializeElements();
    }

    /**
     * Initialise les éléments DOM
     */
    initializeElements() {
        this.metricSelect = document.getElementById('metric-select');
        this.yearSelect = document.getElementById('year-select');
        
        if (this.metricSelect) {
            this.metricSelect.addEventListener('change', () => this.onMetricChange());
        }
        
        if (this.yearSelect) {
            this.yearSelect.addEventListener('change', () => this.onYearChange());
        }
    }

    /**
     * Gère le changement de métrique
     */
    onMetricChange() {
        this.currentMetric = this.metricSelect.value;
        this.notifyListeners('metric', this.currentMetric);
    }

    /**
     * Gère le changement d'année
     */
    onYearChange() {
        this.currentYear = parseInt(this.yearSelect.value);
        
        // Si la métrique contient une année, la mettre à jour
        if (this.currentMetric.match(/_\d{4}$/)) {
            const baseMetric = this.currentMetric.replace(/_\d{4}$/, '');
            this.currentMetric = `${baseMetric}_${this.currentYear}`;
            
            // Mettre à jour le select si l'option existe
            const option = this.metricSelect.querySelector(`option[value="${this.currentMetric}"]`);
            if (option) {
                this.metricSelect.value = this.currentMetric;
            }
        }
        
        this.notifyListeners('year', this.currentYear);
    }

    /**
     * Ajoute un listener pour les changements
     * @param {Function} callback - Fonction à appeler lors d'un changement
     */
    addListener(callback) {
        this.listeners.push(callback);
    }

    /**
     * Notifie tous les listeners
     * @param {string} type - Type de changement ('metric' ou 'year')
     * @param {any} value - Nouvelle valeur
     */
    notifyListeners(type, value) {
        this.listeners.forEach(listener => {
            listener(type, value);
        });
    }

    /**
     * Retourne la métrique courante
     * @returns {string}
     */
    getCurrentMetric() {
        return this.currentMetric;
    }

    /**
     * Retourne l'année courante
     * @returns {number}
     */
    getCurrentYear() {
        return this.currentYear;
    }

    /**
     * Définit la métrique courante
     * @param {string} metric - Nouvelle métrique
     */
    setMetric(metric) {
        this.currentMetric = metric;
        if (this.metricSelect) {
            this.metricSelect.value = metric;
        }
        this.notifyListeners('metric', metric);
    }

    /**
     * Définit l'année courante
     * @param {number} year - Nouvelle année
     */
    setYear(year) {
        this.currentYear = year;
        if (this.yearSelect) {
            this.yearSelect.value = year.toString();
        }
        this.notifyListeners('year', year);
    }

    /**
     * Récupère les options de métriques disponibles
     * @returns {Array} Liste des métriques
     */
    getAvailableMetrics() {
        if (!this.metricSelect) return [];
        
        return Array.from(this.metricSelect.options).map(option => ({
            value: option.value,
            label: option.textContent,
            group: option.parentElement.label
        }));
    }

    /**
     * Récupère les années disponibles
     * @returns {Array} Liste des années
     */
    getAvailableYears() {
        if (!this.yearSelect) return [];
        
        return Array.from(this.yearSelect.options).map(option => 
            parseInt(option.value)
        );
    }

    /**
     * Réinitialise les filtres aux valeurs par défaut
     */
    reset() {
        this.setMetric('prix_m2_median_2024');
        this.setYear(2024);
    }

    /**
     * Désactive les filtres
     */
    disable() {
        if (this.metricSelect) {
            this.metricSelect.disabled = true;
        }
        if (this.yearSelect) {
            this.yearSelect.disabled = true;
        }
    }

    /**
     * Active les filtres
     */
    enable() {
        if (this.metricSelect) {
            this.metricSelect.disabled = false;
        }
        if (this.yearSelect) {
            this.yearSelect.disabled = false;
        }
    }

    /**
     * Vérifie si une métrique est temporelle (contient une année)
     * @param {string} metric - Métrique à vérifier
     * @returns {boolean}
     */
    isTemporalMetric(metric) {
        return /_\d{4}$/.test(metric);
    }

    /**
     * Extrait l'année d'une métrique temporelle
     * @param {string} metric - Métrique
     * @returns {number|null} Année ou null
     */
    extractYearFromMetric(metric) {
        const match = metric.match(/_(\d{4})$/);
        return match ? parseInt(match[1]) : null;
    }

    /**
     * Crée une métrique avec une année spécifique
     * @param {string} baseMetric - Métrique de base
     * @param {number} year - Année
     * @returns {string} Métrique avec année
     */
    createMetricWithYear(baseMetric, year) {
        // Enlever l'année existante si présente
        const base = baseMetric.replace(/_\d{4}$/, '');
        return `${base}_${year}`;
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Filters;
}
