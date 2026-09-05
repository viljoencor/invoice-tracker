"""add invoice idempotency key and client soft delete

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-02 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable: existing rows have no idempotency key; only new invoices set one.
    op.add_column("invoices", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.create_unique_constraint(
        "uq_invoices_org_idem", "invoices", ["org_id", "idempotency_key"]
    )

    # Soft delete: preserves an audit trail instead of destroying the client row.
    op.add_column(
        "clients", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("clients", "deleted_at")
    op.drop_constraint("uq_invoices_org_idem", "invoices", type_="unique")
    op.drop_column("invoices", "idempotency_key")
