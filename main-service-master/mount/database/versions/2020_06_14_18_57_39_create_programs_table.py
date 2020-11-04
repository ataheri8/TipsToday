"""create programs table

Revision ID: be4d5257ce90
Revises: c03e87a1d193
Create Date: 2020-06-14 18:57:39.964152

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be4d5257ce90'
down_revision = 'c03e87a1d193'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            program_id SERIAL PRIMARY KEY,
            program_name TEXT NOT NULL,
            program_type TEXT NOT NULL,
            program_status TEXT NOT NULL,
            subprogram_id TEXT NOT NULL,
            card_type TEXT NOT NULL,
            network TEXT NOT NULL,
            sponsoring_bank TEXT NOT NULL,
            program_bin TEXT NOT NULL,
            program_bin_range TEXT NOT NULL,
            processor TEXT NOT NULL,
            printer TEXT NOT NULL,
            printer_client_id TEXT,
            printer_package_id TEXT,
            card_order_type TEXT NOT NULL,
            card_order_frequency TEXT NOT NULL,
            pin_enabled INTEGER NOT NULL DEFAULT 0,
            pin_change INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)


def downgrade():
    op.execute("""DROP TABLE IF EXISTS programs""")
