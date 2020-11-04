"""create customers table

Revision ID: 557b43bf907e
Revises: 614bc035380b
Create Date: 2020-03-26 05:54:03.616409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '557b43bf907e'
down_revision = '614bc035380b'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS customers_customer_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER DEFAULT nextval('customers_customer_id_seq') PRIMARY KEY,
            customer_status TEXT NOT NULL,
            identifier TEXT NOT NULL,
            passphrase VARCHAR(255) NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_customers_identifier ON customers(identifier)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_customers_identifier""")
    op.execute("""DROP TABLE IF EXISTS customers""")
    op.execute("""DROP SEQUENCE IF EXISTS customers_customer_id_seq""")


