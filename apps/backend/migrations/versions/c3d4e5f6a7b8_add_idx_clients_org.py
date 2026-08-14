"""add idx_clients_org index

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-08-10 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_clients_org", "clients", ["org_id"])


def downgrade() -> None:
    op.drop_index("idx_clients_org", table_name="clients")
