"""Add Celery task_id in Analysis

Revision ID: e4159237369c
Revises: 045401a0856b
Create Date: 2023-01-04 11:43:56.710394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4159237369c'
down_revision = '045401a0856b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Analysis', sa.Column('task_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Analysis', 'task_id')
    # ### end Alembic commands ###
