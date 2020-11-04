"""create admins table

Revision ID: 614bc035380b
Revises: 009303096e91
Create Date: 2020-03-21 21:22:09.747354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '614bc035380b'
down_revision = '009303096e91'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS admins_admin_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER DEFAULT nextval('admins_admin_id_seq') PRIMARY KEY,
            admin_status TEXT NOT NULL,
            identifier TEXT NOT NULL,
            passphrase VARCHAR(255) NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            level TEXT NOT NULL,
            title TEXT,
            client_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_admins_identifier ON admins(identifier)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_admins_by_client_id ON admins(client_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_admins_identifier""")
    op.execute("""DROP INDEX IF EXISTS idx_admins_by_client_id""")    
    op.execute("""DROP TABLE admins""")
    op.execute("""DROP SEQUENCE IF EXISTS admins_admin_id_seq""")


