"""create client contacts table

Revision ID: 99544fc5fecd
Revises: 8a786668b701
Create Date: 2020-02-27 16:20:30.769150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99544fc5fecd'
down_revision = '8a786668b701'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                contact_name TEXT PRIMARY KEY,
                contact_phone TEXT NOT NULL,
                contact_email TEXT NOT NULL, 
                client_id INTEGER NOT NULL,
                company_name TEXT
            )
        """)


def downgrade():
    op.execute("""DROP TABLE IF EXISTS contacts""")
