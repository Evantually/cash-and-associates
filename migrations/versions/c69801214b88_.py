"""empty message

Revision ID: c69801214b88
Revises: f392549a085c
Create Date: 2021-12-09 14:19:39.001375

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c69801214b88'
down_revision = 'f392549a085c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('calendar_event', sa.Column('category', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('calendar_event', 'category')
    # ### end Alembic commands ###