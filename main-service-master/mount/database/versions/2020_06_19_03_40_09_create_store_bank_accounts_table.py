"""create store bank accounts table

Revision ID: b20b6f31359f
Revises: 1fb386e3c41b
Create Date: 2020-06-19 03:40:09.235221

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b20b6f31359f'
down_revision = '1fb386e3c41b'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS store_bank_accounts (
            store_bank_account_id SERIAL PRIMARY KEY,
            store_id INTEGER NOT NULL,
            transit_number TEXT NOT NULL,
            institution_number TEXT NOT NULL,
            account_number TEXT NOT NULL,
            store_bank_account_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_store_bank_accounts_store_id ON store_bank_accounts(store_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_store_bank_accounts_store_id""")
    op.execute("""DROP TABLE store_bank_accounts""")
