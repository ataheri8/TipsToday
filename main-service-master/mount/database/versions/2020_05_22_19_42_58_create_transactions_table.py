"""create transactions table

Revision ID: c03e87a1d193
Revises: a78b86db5da7
Create Date: 2020-05-31 19:42:58.239204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c03e87a1d193'
down_revision = 'a78b86db5da7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            rec_id SERIAL PRIMARY KEY,
            txn_id TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            proxy TEXT NOT NULL,
            txn_amount NUMERIC(14,4) NOT NULL,
            txn_status TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            event_type TEXT NOT NULL,
    	    currency_code TEXT NOT NULL,
	    description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_txns_customer_id ON transactions(customer_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_txns_txn_id ON transactions(txn_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_txns_proxy ON transactions(proxy)""")



def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_txns_customer_id""")
    op.execute("""DROP INDEX IF EXISTS idx_txns_txn_id""")
    op.execute("""DROP INDEX IF EXISTS idx_txns_proxy""")
    op.execute("""DROP TABLE transactions""")



