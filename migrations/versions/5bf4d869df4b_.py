"""empty message

Revision ID: 5bf4d869df4b
Revises: 81ea134ef223
Create Date: 2021-08-01 02:56:52.897840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bf4d869df4b'
down_revision = '81ea134ef223'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('transaction_type', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'transaction_type')
    # ### end Alembic commands ###
