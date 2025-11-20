/**
 * Gestion de l'interface utilisateur
 */

class UI {
    constructor(api) {
        this.api = api;
        this.currentArrondissement = null;
    }

    async showDetailPanel(numero) {
        try {
            this.currentArrondissement = numero;
            
            showLoading();
            
            // Charger les données
            const data = await this.api.getArrondissement(numero);
            
            hideLoading();
            
            if (!data) {
                this.showError("Données non disponibles");
                return;
            }
            
            // Construire le contenu
            const content = this.buildDetailContent(numero, data);
            
            // Afficher dans le panneau
            const detailContent = document.getElementById('detail-content');
            const detailPanel = document.getElementById('detail-panel');
            
            if (detailContent) {
                detailContent.innerHTML = content;
            }
            
            if (detailPanel) {
                detailPanel.classList.remove('hidden');
            }
            
        } catch (error) {
            hideLoading();
            log(`❌ Erreur affichage détails: ${error.message}`, 'error');
            this.showError("Erreur de chargement");
        }
    }

    buildDetailContent(numero, data) {
        return `
            <h3>${numero}e arrondissement</h3>
            
            ${this.buildPrixSection(data)}
            ${this.buildLogementSection(data)}
            ${this.buildTypologieSection(data)}
            ${this.buildTransportSection(data)}
            ${this.buildPollutionSection(data)}
        `;
    }

    buildPrixSection(data) {
        const year = '2024'; // Par défaut
        
        return `
            <div class="detail-section">
                <h4>💰 Prix & Marché</h4>
                ${this.buildDetailRow('Prix/m² médian', formatPricePerM2(data[`prix_m2_median_${year}`]))}
                ${this.buildDetailRow('Prix médian', formatPrice(data[`prix_median_${year}`]))}
                ${this.buildDetailRow('Nb de ventes', formatNumber(data[`nb_ventes_${year}`]))}
                ${data.evolution_prix_2020_2024_pct ? this.buildDetailRow('Évolution 2020-2024', formatPercent(data.evolution_prix_2020_2024_pct)) : ''}
                ${data.tendance_prix_m2 ? this.buildDetailRow('Tendance', data.tendance_prix_m2) : ''}
                ${data.volatilite_prix_m2 ? this.buildDetailRow('Volatilité', data.volatilite_prix_m2.toFixed(2)) : ''}
            </div>
        `;
    }

    buildLogementSection(data) {
        return `
            <div class="detail-section">
                <h4>🏢 Logements Sociaux</h4>
                ${this.buildDetailRow('Nb (APUR)', formatNumber(data.nb_logements_sociaux_apur))}
                ${data.part_logements_sociaux_apur_pct ? this.buildDetailRow('Part (%)', formatPercent(data.part_logements_sociaux_apur_pct)) : ''}
                ${data.estimation_logement_social_pct ? this.buildDetailRow('Estimation', data.estimation_logement_social_pct) : ''}
            </div>
        `;
    }

    buildTypologieSection(data) {
        const year = '2024';
        
        return `
            <div class="detail-section">
                <h4>🏠 Typologie</h4>
                ${this.buildDetailRow('Appartements', formatNumber(data[`nb_appartements_${year}`] || data.nb_appartements_2024))}
                ${this.buildDetailRow('Maisons', formatNumber(data[`nb_maisons_${year}`] || data.nb_maisons_2024))}
                ${data.pct_appartements ? this.buildDetailRow('% Appartements', formatPercent(data.pct_appartements)) : ''}
                ${data.nb_pieces_moyen ? this.buildDetailRow('Nb pièces moyen', data.nb_pieces_moyen.toFixed(1)) : ''}
                
                ${(data[`nb_T1_${year}`] || data[`nb_T2_${year}`]) ? `
                    <div style="margin-top: 1rem; padding-left: 1rem; border-left: 3px solid #667eea;">
                        <strong>Répartition par taille:</strong>
                        ${data[`nb_T1_${year}`] ? this.buildDetailRow('T1/Studio', formatNumber(data[`nb_T1_${year}`])) : ''}
                        ${data[`nb_T2_${year}`] ? this.buildDetailRow('T2', formatNumber(data[`nb_T2_${year}`])) : ''}
                        ${data[`nb_T3_${year}`] ? this.buildDetailRow('T3', formatNumber(data[`nb_T3_${year}`])) : ''}
                        ${data[`nb_T4_${year}`] ? this.buildDetailRow('T4', formatNumber(data[`nb_T4_${year}`])) : ''}
                        ${data[`nb_T5plus_${year}`] ? this.buildDetailRow('T5+', formatNumber(data[`nb_T5plus_${year}`])) : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    buildTransportSection(data) {
        return `
            <div class="detail-section">
                <h4>🚇 Transport</h4>
                ${this.buildDetailRow('Stations métro', formatNumber(data.nb_stations_metro))}
                ${this.buildDetailRow('Lignes métro', formatNumber(data.nb_lignes_metro))}
                ${data.lignes_metro ? this.buildDetailRow('Lignes', data.lignes_metro) : ''}
                ${data.nb_lignes_rer ? this.buildDetailRow('Lignes RER', formatNumber(data.nb_lignes_rer)) : ''}
                ${data.lignes_rer ? this.buildDetailRow('RER', data.lignes_rer) : ''}
                ${data.trafic_total_metro ? this.buildDetailRow('Trafic total', formatNumber(data.trafic_total_metro) + ' pass./an') : ''}
            </div>
        `;
    }

    buildPollutionSection(data) {
        return `
            <div class="detail-section">
                <h4>🌫️ Qualité de l'air</h4>
                ${data.qualite_air_dominante ? this.buildDetailRow('Qualité dominante', data.qualite_air_dominante) : ''}
                ${data.no2_moyen ? this.buildDetailRow('NO₂ moyen', data.no2_moyen.toFixed(1) + ' µg/m³') : ''}
                ${data.pm10_moyen ? this.buildDetailRow('PM10 moyen', data.pm10_moyen.toFixed(1) + ' µg/m³') : ''}
                ${data.o3_moyen ? this.buildDetailRow('O₃ moyen', data.o3_moyen.toFixed(1) + ' µg/m³') : ''}
            </div>
        `;
    }

    buildDetailRow(label, value) {
        if (value === 'N/A' || value === null || value === undefined) {
            return '';
        }
        
        return `
            <div class="detail-row">
                <span class="detail-label">${label}</span>
                <span class="detail-value">${value}</span>
            </div>
        `;
    }

    showError(message) {
        const detailContent = document.getElementById('detail-content');
        if (detailContent) {
            detailContent.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: #dc2626;">
                    <h3>⚠️ Erreur</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    async updateStatsPanel(metric) {
        try {
            // Récupérer toutes les données
            const allData = await this.api.getAllArrondissements();
            
            if (!allData || allData.length === 0) {
                document.getElementById('stats-content').innerHTML = '<p>Pas de données</p>';
                return;
            }
            
            // Calculer les stats pour cette métrique
            const values = allData.map(arr => arr[metric]).filter(v => v !== null && v !== undefined);
            
            if (values.length === 0) {
                document.getElementById('stats-content').innerHTML = '<p>Pas de données pour cette métrique</p>';
                return;
            }
            
            const min = Math.min(...values);
            const max = Math.max(...values);
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            
            document.getElementById('stats-content').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Minimum</span>
                    <span class="stat-value">${formatValueForMetric(min, metric)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Maximum</span>
                    <span class="stat-value">${formatValueForMetric(max, metric)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Moyenne</span>
                    <span class="stat-value">${formatValueForMetric(avg, metric)}</span>
                </div>
            `;
            
        } catch (error) {
            log(`❌ Erreur stats: ${error.message}`, 'error');
        }
    }
}

// Fonction pour fermer le panneau de détails
function closeDetailPanel() {
    const panel = document.getElementById('detail-panel');
    if (panel) {
        panel.classList.add('hidden');
    }
}