"""bulk_transfer

Revision ID: 6524305ed1cc
Revises: e43cc283c897
Create Date: 2020-04-01 01:58:34.842084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6524305ed1cc'
down_revision = 'e43cc283c897'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
                    CREATE TABLE IF NOT EXISTS customer_card_info(
                        mobile VARCHAR(10) PRIMARY KEY,
                        employee_id INTEGER,
                        client_id INTEGER NOT NULL,
                        proxy INTEGER,
                        first TEXT NOT NULL,
                        last TEXT NOT NULL,
                        amount FLOAT NOT NULL DEFAULT 0
                    )
               """)


def downgrade():
    op.execute("""DROP TABLE IF EXISTS customer_card_info""")
