"""empty message

Revision ID: 732b6fffe866
Revises: c57244d851ff
Create Date: 2021-08-18 10:34:41.293945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '732b6fffe866'
down_revision = 'c57244d851ff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'job', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'job', type_='foreignkey')
    op.drop_column('job', 'user_id')
    # ### end Alembic commands ###
