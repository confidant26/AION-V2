"""create assets table

Revision ID: 188799405e6c
Revises:
Create Date: 2026-07-28 18:07:03.474764
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "188799405e6c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("market", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_assets_active"),
        "assets",
        ["active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_asset_type"),
        "assets",
        ["asset_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_country"),
        "assets",
        ["country"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_currency"),
        "assets",
        ["currency"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_exchange"),
        "assets",
        ["exchange"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_industry"),
        "assets",
        ["industry"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_isin"),
        "assets",
        ["isin"],
        unique=True,
    )
    op.create_index(
        op.f("ix_assets_market"),
        "assets",
        ["market"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_sector"),
        "assets",
        ["sector"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_symbol"),
        "assets",
        ["symbol"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assets_symbol"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_sector"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_market"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_isin"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_industry"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_exchange"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_currency"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_country"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_asset_type"),
        table_name="assets",
    )
    op.drop_index(
        op.f("ix_assets_active"),
        table_name="assets",
    )
    op.drop_table("assets")