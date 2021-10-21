"""empty message

Revision ID: 4fe034e8487a
Revises: 596cac2bba57
Create Date: 2021-10-21 11:56:59.307826

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fe034e8487a'
down_revision = '596cac2bba57'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('track', sa.Column('meet_location', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('track', 'meet_location')
    # ### end Alembic commands ###
