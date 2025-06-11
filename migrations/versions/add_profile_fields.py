"""Add missing fields to StudentProfile and InstructorProfile

Revision ID: add_profile_fields
Revises: add_quiz_answer_table
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_profile_fields'
down_revision = 'add_quiz_answer_table'
branch_labels = None
depends_on = None

def upgrade():
    # Only add years_of_experience if missing
    op.add_column('instructor_profile', sa.Column('years_of_experience', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('instructor_profile', 'years_of_experience') 