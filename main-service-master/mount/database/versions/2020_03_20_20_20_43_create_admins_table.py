"""create admins table

Revision ID: 009303096e91
Revises: 8a786668b701
Create Date: 2020-03-20 20:20:43.277942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009303096e91'
down_revision = '8a786668b701'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""CREATE SEQUENCE IF NOT EXISTS admins_super_admin_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS super_admins (
            super_admin_id INTEGER DEFAULT nextval('admins_super_admin_id_seq') PRIMARY KEY,
            super_admin_status TEXT NOT NULL,
            identifier TEXT NOT NULL,
            passphrase VARCHAR(255) NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_super_admins_identifier ON super_admins(identifier)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_super_admins_identifier""")
    op.execute("""DROP TABLE super_admins""")
    op.execute("""DROP SEQUENCE IF EXISTS admins_super_admin_id_seq""")


