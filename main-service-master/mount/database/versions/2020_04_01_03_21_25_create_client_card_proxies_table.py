"""create client_card_proxies table

Revision ID: a95364cde997
Revises: 557b43bf907e
Create Date: 2020-04-01 03:21:25.499635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a95364cde997'
down_revision = '557b43bf907e'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_card_proxies (
            rec_id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            proxy TEXT NOT NULL,
            proxy_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_client_proxies_client_id ON client_card_proxies(client_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_client_proxies_proxy ON client_card_proxies(proxy)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_client_proxies_proxy_status ON client_card_proxies(proxy, proxy_status)""")

def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_client_proxies_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_client_proxies_proxy""")
    op.execute("""DROP INDEX IF EXISTS idx_client_proxies_proxy_status""")
    op.execute("""DROP TABLE client_card_proxies""")
