"""Add timestamps to quiz submission

Revision ID: add_timestamps_to_quiz_submission
Revises: add_time_limit_to_quiz
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_timestamps_to_quiz_submission'
down_revision = 'add_time_limit_to_quiz'
branch_labels = None
depends_on = None


def upgrade():
    # Add start_time and end_time columns to quiz_submission table
    op.add_column('quiz_submission', sa.Column('start_time', sa.DateTime(), nullable=True))
    op.add_column('quiz_submission', sa.Column('end_time', sa.DateTime(), nullable=True))


def downgrade():
    # Remove start_time and end_time columns from quiz_submission table
    op.drop_column('quiz_submission', 'end_time')
    op.drop_column('quiz_submission', 'start_time') 