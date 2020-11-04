"""create stores table

Revision ID: b35ca07d32db
Revises: a95364cde997
Create Date: 2020-04-25 04:33:36.483009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b35ca07d32db'
down_revision = 'a95364cde997'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE SEQUENCE IF NOT EXISTS stores_store_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")
    op.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            store_id INTEGER DEFAULT nextval('stores_store_id_seq') PRIMARY KEY,
            client_id INTEGER NOT NULL,
            store_status TEXT NOT NULL,
            store_name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            card_load_identifier TEXT NOT NULL,
            pad_weekday INTEGER NOT NULL,
            olson_timezone TEXT,
            admins JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_stores_by_client_id ON stores(client_id)""")

def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_stores_by_client_id""")
    op.execute("""DROP TABLE stores""")
    op.execute("""DROP SEQUENCE IF EXISTS stores_store_id_seq""")

