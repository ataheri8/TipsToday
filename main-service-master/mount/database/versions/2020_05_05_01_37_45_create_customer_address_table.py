"""create customer address table

Revision ID: cd56e547e97b
Revises: a4ed823732cd
Create Date: 2020-05-05 01:37:45.827031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd56e547e97b'
down_revision = 'a4ed823732cd'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS customers_address_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS customer_addresses (
            address_id INTEGER DEFAULT nextval('customers_address_id_seq') PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            street TEXT NOT NULL,
            street2 TEXT,
            street3 TEXT,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            country TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            address_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_customer_addresses_customer_id ON customer_addresses(customer_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_customer_addresses_customer_id""")
    op.execute("""DROP TABLE customer_addresses""")
    op.execute("""DROP SEQUENCE IF EXISTS customers_address_id_seq""")



