/**
 * Module de comparaison d'arrondissements
 */

class Comparateur {
    constructor(api, ui) {
        this.api = api;
        this.ui = ui;
        this.arrondissementA = null;
        this.arrondissementB = null;
        this.dataA = null;
        this.dataB = null;
    }

    /**
     * Initialise le mode comparaison
     */
    init() {
        // Ajouter les écouteurs d'événements
        const btnComparer = document.getElementById('btn-comparer');
        const btnFermerComparaison = document.getElementById('btn-fermer-comparaison');
        const selectA = document.getElementById('select-arr-a');
        const selectB = document.getElementById('select-arr-b');

        if (btnComparer) {
            btnComparer.addEventListener('click', () => this.lancerComparaison());
        }

        if (btnFermerComparaison) {
            btnFermerComparaison.addEventListener('click', () => this.fermerComparaison());
        }

        if (selectA) {
            selectA.addEventListener('change', (e) => {
                this.arrondissementA = parseInt(e.target.value);
            });
        }

        if (selectB) {
            selectB.addEventListener('change', (e) => {
                this.arrondissementB = parseInt(e.target.value);
            });
        }

        log('✅ Module de comparaison initialisé', 'success');
    }

    /**
     * Lance la comparaison entre 2 arrondissements
     */
    async lancerComparaison() {
        if (!this.arrondissementA || !this.arrondissementB) {
            alert('Veuillez sélectionner 2 arrondissements');
            return;
        }

        if (this.arrondissementA === this.arrondissementB) {
            alert('Veuillez sélectionner 2 arrondissements différents');
            return;
        }

        try {
            showLoading();

            // Charger les données des 2 arrondissements
            this.dataA = await this.api.getArrondissement(this.arrondissementA);
            this.dataB = await this.api.getArrondissement(this.arrondissementB);

            hideLoading();

            // Analyser et afficher
            this.afficherComparaison();

        } catch (error) {
            hideLoading();
            log(`❌ Erreur comparaison: ${error.message}`, 'error');
            alert(`Erreur lors de la comparaison: ${error.message}`);
        }
    }

    /**
     * Affiche le panneau de comparaison
     */
    afficherComparaison() {
        const panel = document.getElementById('comparison-panel');
        const content = document.getElementById('comparison-content');

        if (!panel || !content) return;

        // Analyser les différences
        const analyse = this.analyserDifferences();

        // Construire le HTML
        content.innerHTML = this.construireHTML(analyse);

        // Afficher le panneau
        panel.classList.remove('hidden');

        log('✅ Comparaison affichée', 'success');
    }

    /**
     * Analyse les différences entre les 2 arrondissements
     */
    analyserDifferences() {
        const categories = {
            prix: this.comparerPrix(),
            logements: this.comparerLogements(),
            transport: this.comparerTransport(),
            pollution: this.comparerPollution(),
            general: this.comparerGeneral()
        };

        // Déterminer le meilleur arrondissement global
        const scores = {
            A: 0,
            B: 0
        };

        Object.values(categories).forEach(cat => {
            cat.items.forEach(item => {
                if (item.meilleur === 'A') scores.A++;
                if (item.meilleur === 'B') scores.B++;
            });
        });

        const meilleurGlobal = scores.A > scores.B ? 'A' : scores.B > scores.A ? 'B' : 'Égalité';

        return {
            categories,
            scores,
            meilleurGlobal
        };
    }

    /**
     * Compare les prix
     */
    comparerPrix() {
        const items = [];

        // Prix/m² 2024
        const prixA = this.dataA.prix_m2_median_2024;
        const prixB = this.dataB.prix_m2_median_2024;

        if (prixA && prixB) {
            items.push({
                critere: 'Prix/m² médian 2024',
                valeurA: formatPricePerM2(prixA),
                valeurB: formatPricePerM2(prixB),
                meilleur: prixA < prixB ? 'A' : 'B', // Moins cher = meilleur
                raison: 'Prix plus accessible'
            });
        }

        // Évolution 2020-2024
        const evolA = this.dataA.evolution_prix_m2_2020_2024_pct;
        const evolB = this.dataB.evolution_prix_m2_2020_2024_pct;

        if (evolA !== null && evolB !== null) {
            items.push({
                critere: 'Évolution prix 2020-2024',
                valeurA: formatPercent(evolA),
                valeurB: formatPercent(evolB),
                meilleur: evolA > evolB ? 'A' : 'B', // Plus de croissance = meilleur investissement
                raison: 'Meilleure valorisation'
            });
        }

        // Tendance
        const tendA = this.dataA.tendance_prix_m2;
        const tendB = this.dataB.tendance_prix_m2;

        if (tendA && tendB) {
            items.push({
                critere: 'Tendance du marché',
                valeurA: tendA,
                valeurB: tendB,
                meilleur: this.comparerTendances(tendA, tendB),
                raison: 'Dynamisme du marché'
            });
        }

        return {
            titre: '💰 Prix & Marché',
            icon: '💰',
            items
        };
    }

    /**
     * Compare les logements
     */
    comparerLogements() {
        const items = [];

        // Logements sociaux APUR
        const socialA = this.dataA.part_logements_sociaux_apur_pct;
        const socialB = this.dataB.part_logements_sociaux_apur_pct;

        if (socialA && socialB) {
            items.push({
                critere: 'Logements sociaux (APUR)',
                valeurA: `${socialA}%`,
                valeurB: `${socialB}%`,
                meilleur: socialA > socialB ? 'A' : 'B', // Plus de mixité sociale = meilleur
                raison: 'Plus de mixité sociale'
            });
        }

        // Nombre de pièces moyen
        const piecesA = this.dataA.nb_pieces_moyen;
        const piecesB = this.dataB.nb_pieces_moyen;

        if (piecesA && piecesB) {
            items.push({
                critere: 'Taille moyenne logements',
                valeurA: `${piecesA} pièces`,
                valeurB: `${piecesB} pièces`,
                meilleur: piecesA > piecesB ? 'A' : 'B',
                raison: 'Logements plus spacieux'
            });
        }

        return {
            titre: '🏠 Logements',
            icon: '🏠',
            items
        };
    }

    /**
     * Compare les transports
     */
    comparerTransport() {
        const items = [];

        // Nombre de lignes métro
        const lignesA = this.dataA.nb_lignes_metro || 0;
        const lignesB = this.dataB.nb_lignes_metro || 0;

        items.push({
            critere: 'Lignes de métro',
            valeurA: `${lignesA} lignes`,
            valeurB: `${lignesB} lignes`,
            meilleur: lignesA > lignesB ? 'A' : 'B',
            raison: 'Meilleure desserte'
        });

        // Nombre de stations
        const stationsA = this.dataA.nb_stations_metro || 0;
        const stationsB = this.dataB.nb_stations_metro || 0;

        items.push({
            critere: 'Stations de métro',
            valeurA: `${stationsA} stations`,
            valeurB: `${stationsB} stations`,
            meilleur: stationsA > stationsB ? 'A' : 'B',
            raison: 'Plus accessible'
        });

        // Trafic
        const traficA = this.dataA.trafic_total_metro || 0;
        const traficB = this.dataB.trafic_total_metro || 0;

        if (traficA && traficB) {
            items.push({
                critere: 'Trafic métro',
                valeurA: formatNumber(traficA),
                valeurB: formatNumber(traficB),
                meilleur: traficA > traficB ? 'A' : 'B',
                raison: 'Plus de fréquentation'
            });
        }

        return {
            titre: '🚇 Transport',
            icon: '🚇',
            items
        };
    }

    /**
     * Compare la pollution
     */
    comparerPollution() {
        const items = [];

        // NO2
        const no2A = this.dataA.no2_moyen;
        const no2B = this.dataB.no2_moyen;

        if (no2A && no2B) {
            items.push({
                critere: 'NO₂ moyen',
                valeurA: `${no2A.toFixed(1)} µg/m³`,
                valeurB: `${no2B.toFixed(1)} µg/m³`,
                meilleur: no2A < no2B ? 'A' : 'B', // Moins = meilleur
                raison: 'Air plus pur'
            });
        }

        // PM10
        const pm10A = this.dataA.pm10_moyen;
        const pm10B = this.dataB.pm10_moyen;

        if (pm10A && pm10B) {
            items.push({
                critere: 'PM10 moyen',
                valeurA: `${pm10A.toFixed(1)} µg/m³`,
                valeurB: `${pm10B.toFixed(1)} µg/m³`,
                meilleur: pm10A < pm10B ? 'A' : 'B',
                raison: 'Moins de particules fines'
            });
        }

        return {
            titre: '🌫️ Qualité de l\'air',
            icon: '🌫️',
            items
        };
    }

    /**
     * Comparaison générale
     */
    comparerGeneral() {
        const items = [];

        // Nombre de ventes 2024
        const ventesA = this.dataA.nb_ventes_2024;
        const ventesB = this.dataB.nb_ventes_2024;

        if (ventesA && ventesB) {
            items.push({
                critere: 'Nombre de ventes 2024',
                valeurA: formatNumber(ventesA),
                valeurB: formatNumber(ventesB),
                meilleur: ventesA > ventesB ? 'A' : 'B',
                raison: 'Marché plus actif'
            });
        }

        return {
            titre: '📊 Général',
            icon: '📊',
            items
        };
    }

    /**
     * Compare 2 tendances
     */
    comparerTendances(tendA, tendB) {
        const ordre = ['Forte baisse', 'Baisse modérée', 'Stable', 'Hausse modérée', 'Forte hausse'];
        const indexA = ordre.indexOf(tendA);
        const indexB = ordre.indexOf(tendB);

        if (indexA === indexB) return 'Égalité';
        return indexA > indexB ? 'A' : 'B';
    }

    /**
     * Construit le HTML de la comparaison
     */
    construireHTML(analyse) {
        const { categories, scores, meilleurGlobal } = analyse;

        let html = `
            <div class="comparison-header">
                <h2>📊 Comparaison détaillée</h2>
                <div class="comparison-vs">
                    <div class="arr-label arr-a">
                        <h3>${this.arrondissementA}e arrondissement</h3>
                        <div class="score">Score: ${scores.A}</div>
                    </div>
                    <div class="vs-badge">VS</div>
                    <div class="arr-label arr-b">
                        <h3>${this.arrondissementB}e arrondissement</h3>
                        <div class="score">Score: ${scores.B}</div>
                    </div>
                </div>
                
                <div class="verdict-global">
                    ${meilleurGlobal === 'A' ? 
                        `<p>🏆 <strong>Le ${this.arrondissementA}e arrondissement</strong> est globalement meilleur</p>` :
                      meilleurGlobal === 'B' ?
                        `<p>🏆 <strong>Le ${this.arrondissementB}e arrondissement</strong> est globalement meilleur</p>` :
                        `<p>⚖️ Les deux arrondissements sont <strong>équivalents</strong></p>`
                    }
                </div>
            </div>

            <div class="comparison-categories">
        `;

        // Pour chaque catégorie
        Object.values(categories).forEach(cat => {
            if (cat.items.length === 0) return;

            html += `
                <div class="comparison-category">
                    <h3>${cat.titre}</h3>
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Critère</th>
                                <th>${this.arrondissementA}e</th>
                                <th>${this.arrondissementB}e</th>
                                <th>Meilleur</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            cat.items.forEach(item => {
                const meilleurClass = item.meilleur === 'A' ? 'meilleur-a' : 
                                     item.meilleur === 'B' ? 'meilleur-b' : 'egalite';

                html += `
                    <tr>
                        <td><strong>${item.critere}</strong></td>
                        <td class="${item.meilleur === 'A' ? 'winner' : ''}">${item.valeurA}</td>
                        <td class="${item.meilleur === 'B' ? 'winner' : ''}">${item.valeurB}</td>
                        <td class="${meilleurClass}">
                            ${item.meilleur === 'A' ? `${this.arrondissementA}e` : 
                              item.meilleur === 'B' ? `${this.arrondissementB}e` : '='
                            }
                            <br/>
                            <small>${item.raison}</small>
                        </td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;
        });

        html += `</div>`;

        return html;
    }

    /**
     * Ferme le panneau de comparaison
     */
    fermerComparaison() {
        const panel = document.getElementById('comparison-panel');
        if (panel) {
            panel.classList.add('hidden');
        }
    }
}