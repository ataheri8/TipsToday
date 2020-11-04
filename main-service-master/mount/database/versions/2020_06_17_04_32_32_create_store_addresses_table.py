"""create store addresses table

Revision ID: 1fb386e3c41b
Revises: be4d5257ce90
Create Date: 2020-06-17 04:32:32.809233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fb386e3c41b'
down_revision = 'be4d5257ce90'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS stores_address_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS store_addresses (
            address_id INTEGER DEFAULT nextval('stores_address_id_seq') PRIMARY KEY,
            store_id INTEGER NOT NULL,
            street TEXT NOT NULL,
            street2 TEXT,
            street3 TEXT,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            country TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            lat TEXT,
            lng TEXT,
            address_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_store_addresses_store_id ON store_addresses(store_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_store_addresses_store_id""")
    op.execute("""DROP TABLE store_addresses""")
    op.execute("""DROP SEQUENCE IF EXISTS stores_address_id_seq""")
