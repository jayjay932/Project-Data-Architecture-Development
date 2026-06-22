"""
Service de chargement des données depuis PostgreSQL
=====================================================
Remplace l'ancien DataLoader basé sur CSV.
Garde EXACTEMENT la même interface publique pour que
les controllers et models n'aient rien à changer.
"""
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy import create_engine, text
import pandas as pd

logger = logging.getLogger(__name__)

# ── Configuration de connexion PostgreSQL ───────────────────
# Doit correspondre au docker-compose.yml
PG_USER = "paris_admin"
PG_PASSWORD = "paris2024"
PG_HOST = "localhost"
PG_PORT = "5433"
PG_DB = "urban_data_explorer"
TABLE_NAME = "arrondissements"

PG_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"


class DataLoader:
    """
    Service singleton pour charger les données depuis PostgreSQL.
    Interface identique à l'ancienne version CSV pour ne rien
    casser dans les controllers/models existants.
    """

    _instance = None
    _engine = None

    def __new__(cls, data_path=None):
        # data_path est conservé pour compatibilité mais n'est plus utilisé
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
            cls._engine = create_engine(PG_URL, pool_pre_ping=True)
        return cls._instance

    @classmethod
    def _get_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(PG_URL, pool_pre_ping=True)
        return cls._engine

    @classmethod
    def load_data(cls, force_reload: bool = False) -> pd.DataFrame:
        """
        Charge toutes les données depuis PostgreSQL (DataFrame).
        Conservé pour compatibilité avec l'ancien code.

        Args:
            force_reload: Ignoré (PostgreSQL est toujours à jour)

        Returns:
            DataFrame contenant toutes les données
        """
        engine = cls._get_engine()
        try:
            df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
            logger.info(f"Données chargées depuis PostgreSQL : {len(df)} arrondissements")
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement depuis PostgreSQL : {e}")
            raise

    @classmethod
    def get_arrondissement(cls, numero: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'un arrondissement spécifique via une
        requête SQL directe (plus rapide qu'un chargement complet).

        Args:
            numero: Numéro de l'arrondissement (1-20)

        Returns:
            Dictionnaire contenant les données ou None si non trouvé
        """
        if not 1 <= numero <= 20:
            logger.warning(f"Numéro d'arrondissement invalide : {numero}")
            return None

        engine = cls._get_engine()
        query = text(f"SELECT * FROM {TABLE_NAME} WHERE arrondissement = :numero")

        with engine.connect() as conn:
            result = conn.execute(query, {"numero": numero})
            row = result.mappings().first()

        if row is None:
            logger.warning(f"Arrondissement {numero} non trouvé dans PostgreSQL")
            return None

        data = dict(row)
        return {k: (None if pd.isna(v) else v) for k, v in data.items()}

    @classmethod
    def get_all_arrondissements(cls) -> List[Dict[str, Any]]:
        """
        Récupère les données de tous les arrondissements.

        Returns:
            Liste de dictionnaires contenant les données
        """
        engine = cls._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {TABLE_NAME} ORDER BY arrondissement"))
            rows = result.mappings().all()

        return [
            {k: (None if pd.isna(v) else v) for k, v in dict(row).items()}
            for row in rows
        ]

    @classmethod
    def get_arrondissements_by_criteria(
        cls,
        prix_min: Optional[float] = None,
        prix_max: Optional[float] = None,
        annee: int = 2024
    ) -> List[Dict[str, Any]]:
        """
        Filtre les arrondissements selon des critères de prix,
        directement via une requête SQL (plus performant).

        Args:
            prix_min: Prix/m² minimum
            prix_max: Prix/m² maximum
            annee: Année de référence

        Returns:
            Liste des arrondissements correspondants
        """
        prix_col = f"prix_m2_median_{annee}"
        engine = cls._get_engine()

        conditions = []
        params = {}

        if prix_min is not None:
            conditions.append(f"{prix_col} >= :prix_min")
            params["prix_min"] = prix_min
        if prix_max is not None:
            conditions.append(f"{prix_col} <= :prix_max")
            params["prix_max"] = prix_max

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = text(f"SELECT * FROM {TABLE_NAME} {where_clause} ORDER BY arrondissement")

        with engine.connect() as conn:
            result = conn.execute(query, params)
            rows = result.mappings().all()

        return [
            {k: (None if pd.isna(v) else v) for k, v in dict(row).items()}
            for row in rows
        ]

    @classmethod
    def get_column_names(cls) -> List[str]:
        """Retourne la liste des noms de colonnes disponibles"""
        engine = cls._get_engine()
        query = text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :table_name ORDER BY ordinal_position"
        )
        with engine.connect() as conn:
            result = conn.execute(query, {"table_name": TABLE_NAME})
            return [row[0] for row in result]

    @classmethod
    def get_stats_summary(cls) -> Dict[str, Any]:
        """
        Retourne un résumé statistique des données via une
        agrégation SQL directe (plus performant qu'un calcul Pandas).

        Returns:
            Dictionnaire avec des statistiques globales
        """
        engine = cls._get_engine()

        with engine.connect() as conn:
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
            nb_arrondissements = count_result.scalar()

            cols_result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = :table_name"
            ), {"table_name": TABLE_NAME})
            nb_colonnes = cols_result.scalar()

            stats_result = conn.execute(text(
                f"""
                SELECT
                    AVG(prix_m2_median_2024) as moyenne,
                    MIN(prix_m2_median_2024) as minimum,
                    MAX(prix_m2_median_2024) as maximum
                FROM {TABLE_NAME}
                """
            ))
            stats_row = stats_result.mappings().first()

        return {
            'nb_arrondissements': nb_arrondissements,
            'colonnes': nb_colonnes,
            'annees_disponibles': [2020, 2021, 2022, 2023, 2024, 2025],
            'prix_m2_moyen_2024': float(stats_row['moyenne']) if stats_row and stats_row['moyenne'] else None,
            'prix_m2_min_2024': float(stats_row['minimum']) if stats_row and stats_row['minimum'] else None,
            'prix_m2_max_2024': float(stats_row['maximum']) if stats_row and stats_row['maximum'] else None,
        }


# Fonction helper pour initialiser le service (conservée pour compatibilité avec app.py)
def initialize_data_loader(data_path=None):
    """
    Initialise le DataLoader.
    data_path est ignoré (conservé pour compatibilité avec l'appel existant
    dans app.py : initialize_data_loader(config.GOLD_DATA_PATH))
    """
    DataLoader._get_engine()
    logger.info(f"DataLoader initialisé avec PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})")
