"""empty message

Revision ID: 7b2655d432eb
Revises: 3215e476a33a
Create Date: 2020-06-29 19:38:37.997962

"""

# revision identifiers, used by Alembic.
revision = '7b2655d432eb'
down_revision = '3215e476a33a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nick', sa.String(length=50), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('nick', name=op.f('uq_users_nick'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###