"""add_simulations_table

Revision ID: f3cc6b3b2a94
Revises: e5f6a7b8c9d0
Create Date: 2026-01-24 16:58:32.226256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3cc6b3b2a94'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'simulation',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('portfolio_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        # Request params
        sa.Column('horizon_years', sa.Integer(), nullable=False),
        sa.Column('num_paths', sa.Integer(), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),
        sa.Column('scenario', sa.String(50), nullable=True),
        sa.Column('rebalance_frequency', sa.String(50), nullable=True),
        sa.Column('mu_type', sa.String(50), nullable=False),
        sa.Column('sample_paths_count', sa.Integer(), nullable=False),
        sa.Column('ruin_threshold', sa.Float(), nullable=True),
        sa.Column('ruin_threshold_type', sa.String(50), nullable=False),
        # Results (stored as JSONB)
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        sa.Column('sample_paths', postgresql.JSONB(), nullable=False),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio.portfolio_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_simulation_portfolio_id', 'simulation', ['portfolio_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_simulation_portfolio_id', table_name='simulation')
    op.drop_table('simulation')
