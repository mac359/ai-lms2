"""Add behavior tracking fields to enrollment

Revision ID: add_behavior_fields_to_enrollment
Revises: add_student_feedback_summary_to_instructor_profile
Create Date: 2024-03-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_behavior_fields_to_enrollment'
down_revision = 'add_student_feedback_summary_to_instructor_profile'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('enrollment', sa.Column('latest_focus_score', sa.Float(), nullable=True))
    op.add_column('enrollment', sa.Column('frustration_level', sa.Float(), nullable=True))
    op.add_column('enrollment', sa.Column('last_updated', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('enrollment', 'latest_focus_score')
    op.drop_column('enrollment', 'frustration_level')
    op.drop_column('enrollment', 'last_updated') 