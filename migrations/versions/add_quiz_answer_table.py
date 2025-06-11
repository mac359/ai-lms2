"""Add quiz_answer table

Revision ID: add_quiz_answer_table
Revises: add_timestamps_to_quiz_submission
Create Date: 2024-03-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_quiz_answer_table'
down_revision = 'add_timestamps_to_quiz_submission'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'quiz_answer',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('quiz_submission.id'), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('question.id'), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True)
    )

def downgrade():
    op.drop_table('quiz_answer') 