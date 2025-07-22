"""Seed users table

Revision ID: 0f04dba152dd
Revises: de9be5e431a5
Create Date: 2025-06-22 08:05:36.776199

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f04dba152dd"
down_revision: Union[str, Sequence[str], None] = "de9be5e431a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        INSERT INTO users (nome, email, hashed_password, role) VALUES 
            ('João Silva', 'joao@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'user'),
            ('Maria Santos', 'maria@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'admin'),
            ('Pedro Oliveira', 'pedro@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'user');
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM users WHERE email IN ('joao@email.com', 'maria@email.com', 'pedro@email.com')"
    )
