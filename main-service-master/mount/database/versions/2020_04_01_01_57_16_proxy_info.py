"""proxy_info

Revision ID: e43cc283c897
Revises: b7bb9ffe22f7
Create Date: 2020-04-01 01:57:16.857177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e43cc283c897'
down_revision = 'b7bb9ffe22f7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
            CREATE TABLE IF NOT EXISTS proxy_info(
                proxy_key INTEGER PRIMARY KEY,
                person_id TEXT,
                client_id INTEGER NOT NULL,
                amount FLOAT NOT NULL DEFAULT 0
            )
    """)

def downgrade():
    op.execute("""DROP TABLE proxy_info""")


