"""create wallets table

Revision ID: 8a786668b701
Revises: d556cca41f20
Create Date: 2020-02-25 05:11:27.405319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a786668b701'
down_revision = 'd556cca41f20'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS wallets_wallet_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            wallet_id INTEGER DEFAULT nextval('wallets_wallet_id_seq') PRIMARY KEY,
            client_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            wallet_status TEXT NOT NULL,
            wallet_name TEXT NOT NULL,
            current_amount NUMERIC(12,2) NOT NULL DEFAULT 0.0,
            alert_amount NUMERIC(12,2) NOT NULL DEFAULT 0.0,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_wallets_client_id ON wallets(client_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_wallets_store_id ON wallets(store_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_wallets_wallet_id_client_id ON wallets(client_id, wallet_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_wallets_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_wallets_wallet_id_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_wallets_store_id""")
    op.execute("""DROP TABLE IF EXISTS wallets""")
    op.execute("""DROP SEQUENCE IF EXISTS wallets_wallet_id_seq""")




