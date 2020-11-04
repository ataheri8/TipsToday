"""create etransfers table

Revision ID: 92630144e593
Revises: 624cc4d6a902
Create Date: 2020-07-03 00:18:04.976569

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92630144e593'
down_revision = '624cc4d6a902'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS etransfers (
            rec_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            etransfer_id TEXT NOT NULL,
            etransfer_amount NUMERIC(13,3) NOT NULL,
            fee_amount NUMERIC(13,3) NOT NULL,
            recipient_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )

    """)
    op.execute("""CREATE INDEX IF NOT EXISTS idx_etransfers_customer_id ON etransfers(customer_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_etransfers_etransfer_id ON etransfers(etransfer_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_etransfers_customer_created_id ON etransfers(customer_id, created_at)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_etransfers_customer_id""")
    op.execute("""DROP INDEX IF EXISTS idx_etransfers_etransfer_id""")
    op.execute("""DROP INDEX IF EXISTS idx_etransfers_customer_created_id""")
    op.execute("""DROP TABLE etransfers""")


