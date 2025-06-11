"""Add subjects_taught to instructor_profile

Revision ID: add_subjects_taught_to_instructor_profile
Revises: add_years_of_experience_to_instructor_profile
Create Date: 2024-03-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_subjects_taught_to_instructor_profile'
down_revision = 'add_years_of_experience_to_instructor_profile'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('instructor_profile', sa.Column('subjects_taught', sa.String(length=200), nullable=True))

def downgrade():
    op.drop_column('instructor_profile', 'subjects_taught') 