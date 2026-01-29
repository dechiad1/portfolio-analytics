"""add_risk_analysis_table

Revision ID: g4dd7c4c3b95
Revises: f3cc6b3b2a94
Create Date: 2026-01-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'g4dd7c4c3b95'
down_revision: Union[str, Sequence[str], None] = 'f3cc6b3b2a94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'risk_analysis',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('portfolio_id', sa.UUID(), nullable=False),
        sa.Column('risks', postgresql.JSONB(), nullable=False),
        sa.Column('macro_climate_summary', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio.portfolio_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_risk_analysis_portfolio_id', 'risk_analysis', ['portfolio_id'])
    op.create_index('idx_risk_analysis_created_at', 'risk_analysis', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_risk_analysis_created_at', table_name='risk_analysis')
    op.drop_index('idx_risk_analysis_portfolio_id', table_name='risk_analysis')
    op.drop_table('risk_analysis')
