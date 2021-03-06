"""empty message

Revision ID: 416962d00e0b
Revises: 0f7b28a7a1e3
Create Date: 2021-11-08 16:45:46.144971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '416962d00e0b'
down_revision = '0f7b28a7a1e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lap_time', sa.Column('stock_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'lap_time', 'car', ['stock_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'lap_time', type_='foreignkey')
    op.drop_column('lap_time', 'stock_id')
    # ### end Alembic commands ###
