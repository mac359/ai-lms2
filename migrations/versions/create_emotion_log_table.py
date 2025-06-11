"""create emotion_log table

Revision ID: create_emotion_log
Revises: add_behavior_fields_to_enrollment
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_emotion_log'
down_revision = 'add_behavior_fields_to_enrollment'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('emotion_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('focus_score', sa.Float(), nullable=True),
        sa.Column('frustration_score', sa.Float(), nullable=True),
        sa.Column('source_data_summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('emotion_log') 