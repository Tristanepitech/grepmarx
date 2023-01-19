"""Add user and object filter in LDAP config

Revision ID: 16d5fffffaca
Revises: 8ab1f2133191
Create Date: 2023-01-19 11:32:00.000152

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16d5fffffaca'
down_revision = '8ab1f2133191'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('LdapConfiguration', sa.Column('user_object_filter', sa.String(), nullable=True))
    op.add_column('LdapConfiguration', sa.Column('group_object_filter', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('LdapConfiguration', 'group_object_filter')
    op.drop_column('LdapConfiguration', 'user_object_filter')
    # ### end Alembic commands ###
