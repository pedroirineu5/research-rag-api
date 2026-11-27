"""Create RPG systems and documents.

Revision ID: 20261126_02
Revises: 20261126_01
"""

import sqlalchemy as sa

from alembic import op

revision = "20261126_02"
down_revision = "20261126_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rpg_systems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("vector_store_id", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("vector_store_id"),
    )
    op.create_index("ix_rpg_systems_slug", "rpg_systems", ["slug"], unique=True)
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "system_id", sa.Integer(), sa.ForeignKey("rpg_systems.id"), nullable=False
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_id", sa.String(length=120), nullable=True, unique=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("chunking_strategy", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error", sa.String(length=1000), nullable=True),
    )
    op.create_index("ix_documents_system_id", "documents", ["system_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_system_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_rpg_systems_slug", table_name="rpg_systems")
    op.drop_table("rpg_systems")
