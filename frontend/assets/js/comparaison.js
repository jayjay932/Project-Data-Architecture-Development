/**
 * Module de comparaison V5
 * Design plus pro + lecture rouge / vert claire.
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

    init() {
        const btnComparer = document.getElementById('btn-comparer');
        const selectA = document.getElementById('select-arr-a');
        const selectB = document.getElementById('select-arr-b');

        if (btnComparer) {
            btnComparer.addEventListener('click', () => this.lancerComparaison());
        }

        if (selectA) {
            selectA.addEventListener('change', (e) => {
                this.arrondissementA = this.parseArrondissement(e.target.value);
            });
        }

        if (selectB) {
            selectB.addEventListener('change', (e) => {
                this.arrondissementB = this.parseArrondissement(e.target.value);
            });
        }

        log('✅ Module de comparaison V5 initialisé', 'success');
    }

    parseArrondissement(value) {
        const n = parseInt(value, 10);
        return Number.isFinite(n) && n >= 1 && n <= 20 ? n : null;
    }

    unwrapApiResponse(response) {
        if (!response) return null;
        if (response.data && typeof response.data === 'object') return response.data;
        return response;
    }

    async lancerComparaison() {
        if (!this.arrondissementA || !this.arrondissementB) {
            alert('Sélectionne 2 arrondissements à comparer.');
            return;
        }

        if (this.arrondissementA === this.arrondissementB) {
            alert('Sélectionne 2 arrondissements différents.');
            return;
        }

        try {
            showLoading();

            const [responseA, responseB] = await Promise.all([
                this.api.getArrondissement(this.arrondissementA),
                this.api.getArrondissement(this.arrondissementB)
            ]);

            this.dataA = this.unwrapApiResponse(responseA);
            this.dataB = this.unwrapApiResponse(responseB);

            hideLoading();

            this.afficherComparaison();
        } catch (error) {
            hideLoading();
            log(`❌ Erreur comparaison: ${error.message}`, 'error');
            alert(`Erreur lors de la comparaison: ${error.message}`);
        }
    }

    afficherComparaison() {
        const panel = document.getElementById('comparison-panel');
        const content = document.getElementById('comparison-content');

        if (!panel || !content) return;

        const groups = this.buildGroups();
        const summary = this.computeSummary(groups);

        content.innerHTML = this.renderComparison(groups, summary);

        const close = document.getElementById('btn-fermer-comparaison');
        if (close) {
            close.addEventListener('click', () => this.fermerComparaison());
        }

        panel.classList.remove('hidden');
        log('✅ Comparaison affichée', 'success');
    }

    getValue(data, ...keys) {
        for (const key of keys) {
            if (data && hasValue(data[key])) {
                return data[key];
            }
        }

        return null;
    }

    buildGroups() {
        return [
            {
                title: '💰 Prix & marché',
                badge: 'Marché immobilier',
                help: 'Vert = plus favorable selon le critère. Rouge = moins favorable.',
                items: [
                    this.numericItem('Prix/m² médian', ['prix_m2_median_2024'], formatPricePerM2, 'lower'),
                    this.numericItem('Prix médian', ['prix_median_2024'], formatPrice, 'lower'),
                    this.numericItem('Nombre de ventes', ['nb_ventes_2024'], formatNumber, 'higher'),
                    this.numericItem('Évolution prix 2020-2024', ['evolution_prix_2020_2024_pct'], formatPercent, 'higher'),
                    this.numericItem('Évolution prix/m² 2023-2024', ['evolution_prix_m2_2023_2024_pct'], formatPercent, 'higher'),
                    this.numericItem('Volatilité prix/m²', ['volatilite_prix_m2'], v => formatDecimal(v, 2), 'lower'),
                    this.textItem('Tendance marché', ['tendance_prix_m2'])
                ].filter(Boolean)
            },
            {
                title: '🏠 Logements & typologie',
                badge: 'Structure du parc',
                help: 'Lecture neutre pour les typologies : elles décrivent le profil du quartier.',
                items: [
                    this.numericItem('Appartements 2024', ['nb_appartements_2024', 'nb_appartement_2024'], formatNumber, 'higher'),
                    this.numericItem('Maisons 2024', ['nb_maisons_2024', 'nb_maison_2024'], formatNumber, 'higher'),

                    this.numericItem('Part T1', ['pct_T1_2024', 'pct_t1_2024'], formatPercent, 'neutral'),
                    this.numericItem('Part T2', ['pct_T2_2024', 'pct_t2_2024'], formatPercent, 'neutral'),
                    this.numericItem('Part T3', ['pct_T3_2024', 'pct_t3_2024'], formatPercent, 'neutral'),
                    this.numericItem('Part T4', ['pct_T4_2024', 'pct_t4_2024'], formatPercent, 'neutral'),
                    this.numericItem('Part T5+', ['pct_T5plus_2024', 'pct_t5plus_2024'], formatPercent, 'neutral'),

                    this.numericItem('Nombre de pièces moyen', ['nb_pieces_moyen'], v => formatDecimal(v, 1), 'higher')
                ].filter(Boolean)
            },
            {
                title: '🏢 Social & accessibilité',
                badge: 'Équilibre social',
                help: 'Les logements sociaux et l’accessibilité sont mis en avant quand ils sont plus élevés.',
                items: [
                    this.numericItem('Logements sociaux APUR', ['nb_logements_sociaux_apur'], formatNumber, 'higher'),
                    this.numericItem('Part logements sociaux', ['part_logements_sociaux_apur_pct'], formatPercent, 'higher'),
                    this.numericItem('Indice accessibilité', ['indice_accessibilite'], v => `${formatDecimal(v, 1)} / 10`, 'higher'),
                    this.numericItem('Tension sociale', ['indice_tension_sociale'], v => `${formatDecimal(v, 1)} / 10`, 'lower'),
                    this.numericItem('Effort d’achat', ['ratio_effort_achat'], v => `${formatDecimal(v, 1)} ans`, 'lower'),
                    this.textItem('Estimation logement social', ['estimation_logement_social_pct'])
                ].filter(Boolean)
            },
            {
                title: '🚇 Transport',
                badge: 'Connexion urbaine',
                help: 'Plus de lignes, stations et trafic indiquent une meilleure connexion.',
                items: [
                    this.numericItem('Stations métro', ['nb_stations_metro'], formatNumber, 'higher'),
                    this.numericItem('Lignes métro', ['nb_lignes_metro'], formatNumber, 'higher'),
                    this.numericItem('Lignes RER', ['nb_lignes_rer'], formatNumber, 'higher'),
                    this.numericItem('Trafic métro annuel', ['trafic_total_metro'], v => `${formatNumber(v)} pass./an`, 'higher'),
                    this.textItem('Lignes métro', ['lignes_metro']),
                    this.textItem('Lignes RER', ['lignes_rer'])
                ].filter(Boolean)
            },
            {
                title: '🌫️ Air & démographie',
                badge: 'Cadre de vie',
                help: 'Pour les polluants, la valeur la plus faible est meilleure.',
                items: [
                    this.numericItem('NO₂ moyen', ['no2_moyen'], v => `${formatDecimal(v, 1)} µg/m³`, 'lower'),
                    this.numericItem('PM10 moyen', ['pm10_moyen'], v => `${formatDecimal(v, 1)} µg/m³`, 'lower'),
                    this.numericItem('O₃ moyen', ['o3_moyen'], v => `${formatDecimal(v, 1)} µg/m³`, 'lower'),
                    this.numericItem('Population 2022', ['population_2022'], v => `${formatNumber(v)} hab.`, 'neutral'),
                    this.numericItem('Densité', ['densite_pop_km2'], v => `${formatNumber(v)} hab/km²`, 'neutral'),
                    this.numericItem('Revenu médian', ['revenu_median'], v => `${formatNumber(v)} €/an`, 'higher'),
                    this.textItem('Qualité air dominante', ['qualite_air_dominante'])
                ].filter(Boolean)
            },
            {
                title: '📊 Indices composites',
                badge: 'Score global',
                help: 'Scores calculés par le backend pour lire rapidement les forces/faiblesses.',
                items: [
                    this.numericItem('Attractivité', ['indice_attractivite'], v => `${formatDecimal(v, 1)} / 10`, 'higher'),
                    this.numericItem('Pression immobilière', ['indice_pression_immo'], v => `${formatDecimal(v, 1)} / 10`, 'lower'),
                    this.numericItem('Accessibilité', ['indice_accessibilite'], v => `${formatDecimal(v, 1)} / 10`, 'higher'),
                    this.numericItem('Tension sociale', ['indice_tension_sociale'], v => `${formatDecimal(v, 1)} / 10`, 'lower')
                ].filter(Boolean)
            }
        ].filter(group => group.items.length);
    }

    numericItem(label, keys, formatter, rule = 'higher') {
        const valueA = this.getValue(this.dataA, ...keys);
        const valueB = this.getValue(this.dataB, ...keys);

        const a = asNumber(valueA);
        const b = asNumber(valueB);

        if (a === null && b === null) return null;

        let winner = 'neutral';

        if (a !== null && b !== null && rule !== 'neutral' && a !== b) {
            if (rule === 'higher') {
                winner = a > b ? 'A' : 'B';
            } else if (rule === 'lower') {
                winner = a < b ? 'A' : 'B';
            }
        }

        return {
            label,
            keys,
            valueA: a !== null ? formatter(a) : this.emptyValue(),
            valueB: b !== null ? formatter(b) : this.emptyValue(),
            rawA: a,
            rawB: b,
            winner,
            rule,
            type: 'numeric'
        };
    }

    textItem(label, keys) {
        const a = this.getValue(this.dataA, ...keys);
        const b = this.getValue(this.dataB, ...keys);

        if (!hasValue(a) && !hasValue(b)) return null;

        return {
            label,
            keys,
            valueA: hasValue(a) ? safeText(a) : this.emptyValue(),
            valueB: hasValue(b) ? safeText(b) : this.emptyValue(),
            rawA: null,
            rawB: null,
            winner: 'neutral',
            rule: 'neutral',
            type: 'text'
        };
    }

    emptyValue() {
        return '—';
    }

    computeSummary(groups) {
        let scoreA = 0;
        let scoreB = 0;
        let neutral = 0;

        groups.forEach(group => {
            group.items.forEach(item => {
                if (item.winner === 'A') scoreA++;
                else if (item.winner === 'B') scoreB++;
                else neutral++;
            });
        });

        return {
            scoreA,
            scoreB,
            neutral,
            total: scoreA + scoreB + neutral,
            winner: scoreA > scoreB ? 'A' : scoreB > scoreA ? 'B' : 'neutral'
        };
    }

    renderComparison(groups, summary) {
        const winnerText =
            summary.winner === 'A'
                ? `${this.arrondissementA}e arrondissement ressort mieux sur les critères comparables.`
                : summary.winner === 'B'
                    ? `${this.arrondissementB}e arrondissement ressort mieux sur les critères comparables.`
                    : `Les deux arrondissements sont équilibrés sur les critères disponibles.`;

        return `
            <button id="btn-fermer-comparaison" type="button" aria-label="Fermer">×</button>

            <div class="comparison-header v5">
                <div class="comparison-topline">
                    <span class="comparison-eyebrow">Analyse comparative</span>
                    <span class="comparison-status">Rouge / Vert</span>
                </div>

                <h2>
                    ${this.arrondissementA}e arrondissement
                    <span>VS</span>
                    ${this.arrondissementB}e arrondissement
                </h2>

                <p>${winnerText}</p>

                <div class="comparison-scoreboard">
                    <div class="score-box ${summary.winner === 'A' ? 'winner' : summary.winner === 'B' ? 'loser' : ''}">
                        <small>${this.arrondissementA}e</small>
                        <strong>${summary.scoreA}</strong>
                        <span>points favorables</span>
                    </div>

                    <div class="score-vs">
                        <b>VS</b>
                        <small>${summary.neutral} neutres</small>
                    </div>

                    <div class="score-box ${summary.winner === 'B' ? 'winner' : summary.winner === 'A' ? 'loser' : ''}">
                        <small>${this.arrondissementB}e</small>
                        <strong>${summary.scoreB}</strong>
                        <span>points favorables</span>
                    </div>
                </div>

                <div class="legend-comparison">
                    <span class="legend-good">● Avantage</span>
                    <span class="legend-bad">● Désavantage</span>
                    <span class="legend-neutral">● Neutre / descriptif</span>
                </div>
            </div>

            <div class="comparison-groups-v5">
                ${groups.map(group => this.renderGroup(group)).join('')}
            </div>
        `;
    }

    renderGroup(group) {
        return `
            <section class="comparison-card-v5">
                <div class="comparison-card-head">
                    <div>
                        <h3>${group.title}</h3>
                        <p>${group.help}</p>
                    </div>
                    <span>${group.badge}</span>
                </div>

                <div class="comparison-lines">
                    ${group.items.map(item => this.renderLine(item)).join('')}
                </div>
            </section>
        `;
    }

    renderLine(item) {
        const classA =
            item.winner === 'A'
                ? 'good'
                : item.winner === 'B'
                    ? 'bad'
                    : 'neutral';

        const classB =
            item.winner === 'B'
                ? 'good'
                : item.winner === 'A'
                    ? 'bad'
                    : 'neutral';

        const iconA =
            item.winner === 'A'
                ? '▲'
                : item.winner === 'B'
                    ? '▼'
                    : '•';

        const iconB =
            item.winner === 'B'
                ? '▲'
                : item.winner === 'A'
                    ? '▼'
                    : '•';

        const reason =
            item.rule === 'higher'
                ? 'Plus élevé = avantage'
                : item.rule === 'lower'
                    ? 'Plus bas = avantage'
                    : 'Lecture descriptive';

        return `
            <div class="comparison-line-v5">
                <div class="comparison-criterion">
                    <strong>${item.label}</strong>
                    <small>${reason}</small>
                </div>

                <div class="comparison-value-v5 ${classA}">
                    <div>
                        <span>${this.arrondissementA}e</span>
                        <b>${item.valueA}</b>
                    </div>
                    <em>${iconA}</em>
                </div>

                <div class="comparison-value-v5 ${classB}">
                    <div>
                        <span>${this.arrondissementB}e</span>
                        <b>${item.valueB}</b>
                    </div>
                    <em>${iconB}</em>
                </div>
            </div>
        `;
    }

    fermerComparaison() {
        const panel = document.getElementById('comparison-panel');
        if (panel) panel.classList.add('hidden');
    }
}