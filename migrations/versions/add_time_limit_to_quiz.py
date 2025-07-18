"""Add time limit and duration to Quiz model

Revision ID: add_time_limit_to_quiz
Revises: 99b40ce5e63b
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_time_limit_to_quiz'
down_revision = '99b40ce5e63b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.add_column(sa.Column('time_limit', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('start_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('end_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.drop_column('end_time')
        batch_op.drop_column('start_time')
        batch_op.drop_column('duration')
        batch_op.drop_column('time_limit')

    # ### end Alembic commands ### 