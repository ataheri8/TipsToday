"""create customer card proxies table

Revision ID: a78b86db5da7
Revises: a3fd0d04fa08
Create Date: 2020-05-22 00:31:16.279834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a78b86db5da7'
down_revision = 'a3fd0d04fa08'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS customer_card_proxies (
            rec_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            proxy TEXT NOT NULL,
            proxy_status TEXT NOT NULL,
            person_id TEXT NOT NULL,
            last4 TEXT,
            expiry TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_customer_proxies_customer_id ON customer_card_proxies(customer_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_customer_proxies_proxy ON customer_card_proxies(proxy)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_customer_proxies_proxy_status ON customer_card_proxies(proxy, proxy_status)""")

def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_customer_proxies_customer_id""")
    op.execute("""DROP INDEX IF EXISTS idx_customer_proxies_proxy""")
    op.execute("""DROP INDEX IF EXISTS idx_customer_proxies_proxy_status""")
    op.execute("""DROP TABLE customer_card_proxies""")


