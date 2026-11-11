"""rename users.neon_user_id -> auth_user_id (Neon Auth -> Better Auth)

Revision ID: i7e8f9a0b1c2
Revises: h6d7e8f9a0b1
"""

from alembic import op

revision = "i7e8f9a0b1c2"
down_revision = "h6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "neon_user_id", new_column_name="auth_user_id")
    op.execute("ALTER TABLE users RENAME CONSTRAINT users_neon_user_id_key TO users_auth_user_id_key")


def downgrade() -> None:
    op.execute("ALTER TABLE users RENAME CONSTRAINT users_auth_user_id_key TO users_neon_user_id_key")
    op.alter_column("users", "auth_user_id", new_column_name="neon_user_id")
