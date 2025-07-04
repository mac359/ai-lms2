"""Add points field to Assignment model

Revision ID: 3dbdb931cf39
Revises: 62e19a5b439b
Create Date: 2025-06-09 12:47:48.230651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dbdb931cf39'
down_revision = '62e19a5b439b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('points', sa.String(length=10), nullable=True))

    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('quiz_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('quiz_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.drop_column('points')

    # ### end Alembic commands ###
