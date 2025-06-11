"""Add years_of_experience to instructor_profile

Revision ID: add_years_of_experience_to_instructor_profile
Revises: add_profile_fields
Create Date: 2024-03-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_years_of_experience_to_instructor_profile'
down_revision = 'add_profile_fields'
branch_labels = None
depends_on = None

def upgrade():
    # years_of_experience already exists, skip adding it
    pass

def downgrade():
    # years_of_experience already exists, skip dropping it
    pass 