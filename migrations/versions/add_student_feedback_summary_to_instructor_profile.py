"""Add student_feedback_summary to instructor_profile

Revision ID: add_student_feedback_summary_to_instructor_profile
Revises: add_subjects_taught_to_instructor_profile
Create Date: 2024-03-19 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_student_feedback_summary_to_instructor_profile'
down_revision = 'add_subjects_taught_to_instructor_profile'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('instructor_profile', sa.Column('student_feedback_summary', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('instructor_profile', 'student_feedback_summary') 