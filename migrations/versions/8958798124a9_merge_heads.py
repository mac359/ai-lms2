"""merge heads

Revision ID: 8958798124a9
Revises: add_is_monitoring_to_enrollment, create_emotion_log
Create Date: 2025-06-09 18:08:41.289398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8958798124a9'
down_revision = ('add_is_monitoring_to_enrollment', 'create_emotion_log')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
