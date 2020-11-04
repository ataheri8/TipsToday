"""client card info

Revision ID: 624c73381210
Revises: 4ba4a0b9a9cc
Create Date: 2020-03-23 17:04:47.392806

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '624c73381210'
down_revision = '4ba4a0b9a9cc'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
                CREATE TABLE IF NOT EXISTS card_info (
                    card_identifier INTEGER PRIMARY KEY,
                    card_holder_name TEXT NOT NULL,
                    cleansed_pan TEXT NOT NULL,
                    client_id Integer,
                    shipment_id INTEGER NOT NULL
                    )
            """)


def downgrade():
    op.execute("""DROP TABLE card_info""")
