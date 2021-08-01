"""empty message

Revision ID: 79e4fbec6640
Revises: 5bf4d869df4b
Create Date: 2021-08-01 04:00:23.225287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79e4fbec6640'
down_revision = '5bf4d869df4b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('total', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'total')
    # ### end Alembic commands ###