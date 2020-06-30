"""empty message

Revision ID: d2e31eefa2cb
Revises: 63abf4a91d17
Create Date: 2020-06-30 03:16:36.066617

"""

# revision identifiers, used by Alembic.
revision = 'd2e31eefa2cb'
down_revision = '63abf4a91d17'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bulletevent') as batch_op:
        batch_op.create_foreign_key('fk_bulletevent_szMd5_demo', 'demo', ['szMd5'], ['szMd5'])
    with op.batch_alter_table('obituary') as batch_op:
        batch_op.create_foreign_key('fk_obituary_szMd5_demo', 'demo', ['szMd5'], ['szMd5'])
    with op.batch_alter_table('player') as batch_op:
        batch_op.create_foreign_key('fk_player_szMd5_demo', 'demo', ['szMd5'], ['szMd5'])
    with op.batch_alter_table('revive') as batch_op:
        batch_op.create_foreign_key('fk_revive_szMd5_demo', 'demo', ['szMd5'], ['szMd5'])
    with op.batch_alter_table('roundstats') as batch_op:
        batch_op.create_foreign_key('fk_roundstats_szMd5_demo', 'demo', ['szMd5'], ['szMd5'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('roundstats') as batch_op:
        batch_op.drop_constraint('fk_roundstats_szMd5_demo', type_='foreignkey')
    with op.batch_alter_table('revive') as batch_op:
        batch_op.drop_constraint('fk_revive_szMd5_demo', type_='foreignkey')
    with op.batch_alter_table('player') as batch_op:
        batch_op.drop_constraint('fk_player_szMd5_demo', type_='foreignkey')
    with op.batch_alter_table('obituary') as batch_op:
        batch_op.drop_constraint('fk_obituary_szMd5_demo', type_='foreignkey')
    with op.batch_alter_table('bulletevent') as batch_op:
        batch_op.drop_constraint('fk_bulletevent_szMd5_demo', type_='foreignkey')
    # ### end Alembic commands ###
