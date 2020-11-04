"""etransfer recipients table create

Revision ID: 747939c460c1
Revises: 626466655f3b
Create Date: 2020-06-27 18:56:26.057978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '747939c460c1'
down_revision = '626466655f3b'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS etransfer_recipients (
            recipient_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            recipient_name TEXT NOT NULL,
            email_address TEXT NOT NULL,
            security_question TEXT NOT NULL,
            security_answer TEXT NOT NULL,
            recipient_status TEXT NOT NULL,
            dc_contact_id TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )

    """)
    op.execute("""CREATE INDEX IF NOT EXISTS idx_etransfer_recipients_customer_id ON etransfer_recipients(customer_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_etransfer_recipients_customer_id""")
    op.execute("""DROP TABLE etransfer_recipients""")

