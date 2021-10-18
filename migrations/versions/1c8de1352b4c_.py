"""empty message

Revision ID: 1c8de1352b4c
Revises: 324ab5a44331
Create Date: 2021-10-17 00:36:46.274274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c8de1352b4c'
down_revision = '324ab5a44331'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('car', sa.Column('make', sa.String(length=64), nullable=True))
    op.add_column('car', sa.Column('model', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('car', 'model')
    op.drop_column('car', 'make')
    # ### end Alembic commands ###
