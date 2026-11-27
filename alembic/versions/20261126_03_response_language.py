"""Store each system's response language.

Revision ID: 20261126_03
Revises: 20261126_02
"""

import sqlalchemy as sa

from alembic import op

revision = "20261126_03"
down_revision = "20261126_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rpg_systems",
        sa.Column(
            "response_language",
            sa.String(length=20),
            nullable=False,
            server_default="pt-BR",
        ),
    )


def downgrade() -> None:
    op.drop_column("rpg_systems", "response_language")
