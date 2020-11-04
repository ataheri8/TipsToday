"""add wallet audit table

Revision ID: c602ac1646c5
Revises: b587a2d0d263
Create Date: 2020-04-30 04:53:01.601548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c602ac1646c5'
down_revision = 'b587a2d0d263'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS wallet_adjustments_history (
            rec_id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            store_id INTEGER NOT NULL,
            store_name TEXT NOT NULL,
            wallet_id INTEGER NOT NULL,
            wallet_name TEXT NOT NULL,
            adjustment_amount NUMERIC(13,3) NOT NULL,
            previous_amount NUMERIC(13,3) NOT NULL,
            total_amount NUMERIC(13,3) NOT NULL,
            entity_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_wah_by_client_id ON wallet_adjustments_history(client_id)""")
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_wah_by_store_id ON wallet_adjustments_history(store_id)""")
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_wah_by_wallet_id ON wallet_adjustments_history(wallet_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_wah_by_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_wah_by_store_id""")
    op.execute("""DROP INDEX IF EXISTS idx_wah_by_wallet_id""")
    op.execute("""DROP TABLE wallet_adjustments_history""")
