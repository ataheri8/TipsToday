"""create clients table

Revision ID: d556cca41f20
Revises:
Create Date: 2020-01-15 02:29:19.797832
Last update: 2020-01-17 03:24:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd556cca41f20'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS clients_client_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER DEFAULT nextval('clients_client_id_seq') PRIMARY KEY,
            client_status TEXT NOT NULL,
            client_name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            program_id INTEGER NOT NULL,
            terms_conditions TEXT NOT NULL,
            csr_instructions TEXT NOT NULL,
            email_alert_address TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_clients_client_name ON clients(client_name)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_clients_client_name""")
    op.execute("""DROP TABLE clients""")
    op.execute("""DROP SEQUENCE IF EXISTS clients_client_id_seq""")


