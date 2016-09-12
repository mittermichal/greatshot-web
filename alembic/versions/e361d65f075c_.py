"""empty message

Revision ID: e361d65f075c
Revises: 
Create Date: 2016-09-12 20:49:46.872527

"""

# revision identifiers, used by Alembic.
revision = 'e361d65f075c'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('renders', sa.Column('title', sa.String(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('renders', 'title')
    ### end Alembic commands ###