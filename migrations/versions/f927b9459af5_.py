"""empty message

Revision ID: f927b9459af5
Revises: 5655f7c23045
Create Date: 2024-04-18 11:52:26.997470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f927b9459af5'
down_revision = '5655f7c23045'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('VulnerableDependency', schema=None) as batch_op:
        batch_op.add_column(sa.Column('has_PoC', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('reachable', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('vendor_Confirmed', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('reachable_and_Exploitable', sa.Boolean(), nullable=True))
        batch_op.drop_column('has_poc')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('VulnerableDependency', schema=None) as batch_op:
        batch_op.add_column(sa.Column('has_poc', sa.BOOLEAN(), nullable=True))
        batch_op.drop_column('reachable_and_Exploitable')
        batch_op.drop_column('vendor_Confirmed')
        batch_op.drop_column('reachable')
        batch_op.drop_column('has_PoC')

    # ### end Alembic commands ###