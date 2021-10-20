"""empty message

Revision ID: f7ef020a6e12
Revises: 1c8de1352b4c
Create Date: 2021-10-17 02:42:09.964368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7ef020a6e12'
down_revision = '1c8de1352b4c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('owned_car', sa.Column('image', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('owned_car', 'image')
    # ### end Alembic commands ###