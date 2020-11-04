"""create fees table

Revision ID: a3fd0d04fa08
Revises: cd56e547e97b
Create Date: 2020-05-07 01:36:59.983605

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3fd0d04fa08'
down_revision = 'cd56e547e97b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE SEQUENCE IF NOT EXISTS fees_fee_id_seq START 10000 INCREMENT BY 1 MINVALUE 10000""")      
    op.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            fee_id INTEGER DEFAULT nextval('fees_fee_id_seq') PRIMARY KEY,
            client_id INT NOT NULL,
            event_type TEXT NOT NULL,
            fee_type TEXT NOT NULL,
            fee_value TEXT NOT NULL,
    	    fee_status TEXT NOT NULL,
	        currency_code TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_fees_client_id ON fees(client_id)""")
    op.execute("""CREATE INDEX IF NOT EXISTS idx_fees_client_event_type ON fees(client_id, event_type)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_fees_client_id""")
    op.execute("""DROP INDEX IF EXISTS idx_fees_client_event_type""")
    op.execute("""DROP TABLE fees""")
    op.execute("""DROP SEQUENCE IF EXISTS fees_fee_id_seq""")





