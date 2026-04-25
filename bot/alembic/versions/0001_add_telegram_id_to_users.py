"""add telegram_id to users

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add telegram_id column to users table
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))

    # Add unique constraint for telegram_id if needed
    op.create_index('idx_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # Add foreign key constraint to telegram table if exists
    # op.create_foreign_key(
    #     'fk_users_telegram', 'users', 'telegram',
    #     ['telegram_id'], ['id']
    # )

def downgrade() -> None:
    # Drop foreign key constraint if it exists
    # op.drop_constraint('fk_users_telegram', 'users', type_='foreignkey')

    # Drop index
    op.drop_index('idx_users_telegram_id', 'users')

    # Drop column
    op.drop_column('users', 'telegram_id')