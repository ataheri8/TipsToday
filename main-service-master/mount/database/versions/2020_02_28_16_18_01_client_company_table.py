"""client_company_table

Revision ID: 4ba4a0b9a9cc
Revises: 99544fc5fecd
Create Date: 2020-02-28 16:18:01.879022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ba4a0b9a9cc'
down_revision = '99544fc5fecd'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_name TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                program_name TEXT NOT NULL,
                pad_account_routing TEXT NOT NULL,
                pad_account_transit TEXT NOT NULL,
                pad_account_number TEXT NOT NULL,
                client_id INTEGER NOT NULL 
            )
        """)


def downgrade():
    op.execute("""DROP TABLE IF EXISTS companies""")
