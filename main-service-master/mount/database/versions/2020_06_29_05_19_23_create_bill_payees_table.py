"""create bill payees table

Revision ID: 624cc4d6a902
Revises: 747939c460c1
Create Date: 2020-06-29 05:19:23.699025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '624cc4d6a902'
down_revision = '747939c460c1'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS bill_payees (
            payee_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            payee_status TEXT NOT NULL,
            payee_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            payee_code TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )

    """)
    op.execute("""CREATE INDEX IF NOT EXISTS idx_bill_payees_customer_id ON bill_payees(customer_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_bill_payees_customer_id""")
    op.execute("""DROP TABLE bill_payees""")


