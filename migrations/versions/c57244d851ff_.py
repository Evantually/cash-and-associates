"""empty message

Revision ID: c57244d851ff
Revises: 1c3ff1e1ad47
Create Date: 2021-08-18 09:27:19.057489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c57244d851ff'
down_revision = '1c3ff1e1ad47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hunting_entry', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'hunting_entry', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'hunting_entry', type_='foreignkey')
    op.drop_column('hunting_entry', 'user_id')
    # ### end Alembic commands ###