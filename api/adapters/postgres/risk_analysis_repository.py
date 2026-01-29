import json
from uuid import UUID

from domain.models.risk_analysis import RiskAnalysis
from domain.ports.risk_analysis_repository import RiskAnalysisRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresRiskAnalysisRepository(RiskAnalysisRepository):
    """PostgreSQL implementation of RiskAnalysisRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, analysis: RiskAnalysis) -> RiskAnalysis:
        """Persist a new risk analysis."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO risk_analysis (id, portfolio_id, risks, macro_climate_summary, model_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, portfolio_id, risks, macro_climate_summary, model_used, created_at
                """,
                (
                    analysis.id,
                    analysis.portfolio_id,
                    json.dumps(analysis.risks),
                    analysis.macro_climate_summary,
                    analysis.model_used,
                    analysis.created_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create risk analysis")

        return self._row_to_risk_analysis(row)

    def get_by_id(self, id: UUID) -> RiskAnalysis | None:
        """Retrieve a risk analysis by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, risks, macro_climate_summary, model_used, created_at
                FROM risk_analysis
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_risk_analysis(row)

    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[RiskAnalysis]:
        """Retrieve all risk analyses for a portfolio, ordered by created_at desc."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, risks, macro_climate_summary, model_used, created_at
                FROM risk_analysis
                WHERE portfolio_id = %s
                ORDER BY created_at DESC
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_risk_analysis(row) for row in rows]

    def delete(self, id: UUID) -> bool:
        """Delete a risk analysis by ID. Returns True if deleted."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM risk_analysis
                WHERE id = %s
                RETURNING id
                """,
                (id,),
            )
            row = cur.fetchone()

        return row is not None

    def get_portfolio_id_for_analysis(self, id: UUID) -> UUID | None:
        """Get the portfolio_id for a risk analysis (for ownership checks)."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_id
                FROM risk_analysis
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return row[0]

    def _row_to_risk_analysis(self, row: tuple) -> RiskAnalysis:
        """Convert a database row to a RiskAnalysis model."""
        return RiskAnalysis(
            id=row[0],
            portfolio_id=row[1],
            risks=row[2],
            macro_climate_summary=row[3],
            model_used=row[4],
            created_at=row[5],
        )
