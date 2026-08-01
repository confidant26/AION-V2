"""create cash flow statements table

Revision ID: 6015862c11c8
Revises: 3c91f346582c
Create Date: 2026-08-01 13:06:59.896816

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6015862c11c8"
down_revision: Union[str, Sequence[str], None] = "3c91f346582c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cash_flow_statements",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "period_end_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "period_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=10),
            nullable=True,
        ),
        sa.Column(
            "operating_cash_flow",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "investing_cash_flow",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "financing_cash_flow",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "capital_expenditure",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "free_cash_flow",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "depreciation_and_amortization",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "stock_based_compensation",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "change_in_working_capital",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "dividends_paid",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "share_repurchases",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "debt_issuance",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "debt_repayment",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.Column(
            "net_change_in_cash",
            sa.Numeric(precision=24, scale=4),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "period_end_date",
            "period_type",
            name="uq_cash_flow_statements_asset_period",
        ),
    )

    op.create_index(
        op.f("ix_cash_flow_statements_asset_id"),
        "cash_flow_statements",
        ["asset_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_cash_flow_statements_id"),
        "cash_flow_statements",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_cash_flow_statements_period_end_date"),
        "cash_flow_statements",
        ["period_end_date"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_cash_flow_statements_period_end_date"),
        table_name="cash_flow_statements",
    )

    op.drop_index(
        op.f("ix_cash_flow_statements_id"),
        table_name="cash_flow_statements",
    )

    op.drop_index(
        op.f("ix_cash_flow_statements_asset_id"),
        table_name="cash_flow_statements",
    )

    op.drop_table("cash_flow_statements")