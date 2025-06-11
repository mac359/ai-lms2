"""
Revision ID: add_is_monitoring_to_enrollment
Revises: 
Create Date: 2024-06-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_monitoring_to_enrollment'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('enrollment', sa.Column('is_monitoring', sa.Boolean(), nullable=True, server_default=sa.false()))

def downgrade():
    op.drop_column('enrollment', 'is_monitoring') 