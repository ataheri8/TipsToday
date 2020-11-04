"""create client flags table

Revision ID: 626466655f3b
Revises: b20b6f31359f
Create Date: 2020-06-20 04:06:36.396367

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '626466655f3b'
down_revision = 'b20b6f31359f'
branch_labels = None
depends_on = None


def upgrade():  
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_flags (
            flag_id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            corp_load INTEGER NOT NULL DEFAULT 0,
            rbc_bilL_payment INTEGER NOT NULL DEFAULT 0,
            load_hub INTEGER NOT NULL DEFAULT 0,
            pad INTEGER NOT NULL DEFAULT 0,
            eft INTEGER NOT NULL DEFAULT 0,
            ach INTEGER NOT NULL DEFAULT 0,
            card_to_card INTEGER NOT NULL DEFAULT 0,
            e_transfer INTEGER NOT NULL DEFAULT 0,
            bill_payment INTEGER NOT NULL DEFAULT 0,
            bank_to_card INTEGER NOT NULL DEFAULT 0,
            card_to_bank INTEGER NOT NULL DEFAULT 0,
            eft_app INTEGER NOT NULL DEFAULT 0,
            ach_app INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    op.execute("""CREATE INDEX IF NOT EXISTS idx_client_flags_client_id ON client_flags(client_id)""")


def downgrade():
    op.execute("""DROP INDEX IF EXISTS idx_client_flags_client_id""")
    op.execute("""DROP TABLE client_flags""")
