"""fix_payment_tx_id

Revision ID: 0004_fix_tx_id
Revises: 0003_add_courses
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_fix_tx_id"
down_revision = "0003_add_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a sequence for payment_transactions.id if it doesn't exist
    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS payment_transactions_id_seq
    """)

    # Set the sequence as the default value for the id column
    op.execute("""
        ALTER TABLE payment_transactions
        ALTER COLUMN id SET DEFAULT nextval('payment_transactions_id_seq')
    """)

    # Set the sequence ownership to the column
    op.execute("""
        ALTER SEQUENCE payment_transactions_id_seq OWNED BY payment_transactions.id
    """)

    # If there are any existing rows without IDs, set them
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM payment_transactions WHERE id IS NULL) THEN
                UPDATE payment_transactions SET id = nextval('payment_transactions_id_seq') WHERE id IS NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove the sequence ownership
    op.execute("""
        ALTER SEQUENCE payment_transactions_id_seq OWNED BY NONE
    """)

    # Remove the default value
    op.execute("""
        ALTER TABLE payment_transactions
        ALTER COLUMN id DROP DEFAULT
    """)

    # Drop the sequence
    op.execute("""
        DROP SEQUENCE IF EXISTS payment_transactions_id_seq
    """)
