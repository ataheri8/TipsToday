"""customer to stores mapping

Revision ID: a4ed823732cd
Revises: c602ac1646c5
Create Date: 2020-05-01 05:05:16.637690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4ed823732cd'
down_revision = 'c602ac1646c5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS customers_mapping (
            rec_id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            map_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_cm_by_client_id ON customers_mapping(client_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_cm_by_store_id ON customers_mapping(store_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_cm_by_customer_id ON customers_mapping(customer_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_cm_by_employee_id_with_client_id ON customers_mapping(client_id, employee_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_cm_by_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_cm_by_store_id""")
    op.execute("""DROP INDEX IF EXISTS idx_cm_by_customer_id""")
    op.execute("""DROP TABLE customers_mapping""")
