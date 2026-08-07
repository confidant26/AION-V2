"""add users portfolios and personal watchlist

Revision ID: 9a7f4e2b1c30
Revises: f819754cc973
Create Date: 2026-08-07 18:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9a7f4e2b1c30"
down_revision: Union[str, Sequence[str], None] = "f819754cc973"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_active"), "users", ["active"], unique=False)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_currency", sa.String(length=16), server_default="USD", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_portfolios_user_name"),
    )
    op.create_index(op.f("ix_portfolios_id"), "portfolios", ["id"], unique=False)
    op.create_index(op.f("ix_portfolios_user_id"), "portfolios", ["user_id"], unique=False)

    op.create_table(
        "portfolio_positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(30, 10), nullable=False),
        sa.Column("average_cost", sa.Numeric(30, 10), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "asset_id", name="uq_portfolio_positions_portfolio_asset"),
    )
    op.create_index(op.f("ix_portfolio_positions_id"), "portfolio_positions", ["id"], unique=False)
    op.create_index(op.f("ix_portfolio_positions_asset_id"), "portfolio_positions", ["asset_id"], unique=False)
    op.create_index(op.f("ix_portfolio_positions_portfolio_id"), "portfolio_positions", ["portfolio_id"], unique=False)

    op.add_column("watchlist_items", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_watchlist_items_user_id_users", "watchlist_items", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index(op.f("ix_watchlist_items_user_id"), "watchlist_items", ["user_id"], unique=False)
    op.drop_constraint("uq_watchlist_items_asset_id", "watchlist_items", type_="unique")
    op.create_unique_constraint("uq_watchlist_items_user_asset", "watchlist_items", ["user_id", "asset_id"])


def downgrade() -> None:
    op.drop_constraint("uq_watchlist_items_user_asset", "watchlist_items", type_="unique")
    op.create_unique_constraint("uq_watchlist_items_asset_id", "watchlist_items", ["asset_id"])
    op.drop_index(op.f("ix_watchlist_items_user_id"), table_name="watchlist_items")
    op.drop_constraint("fk_watchlist_items_user_id_users", "watchlist_items", type_="foreignkey")
    op.drop_column("watchlist_items", "user_id")
    op.drop_table("portfolio_positions")
    op.drop_table("portfolios")
    op.drop_table("users")
