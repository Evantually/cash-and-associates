"""empty message

Revision ID: 3c897a91ad5d
Revises: 4cb5dcf1b43d
Create Date: 2021-10-26 15:01:23.412015

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c897a91ad5d'
down_revision = '4cb5dcf1b43d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('achievement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('image', sa.String(length=256), nullable=True),
    sa.Column('achievement_type', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('achievement_condition',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('check_condition', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('achievement_properties',
    sa.Column('achievement_id', sa.Integer(), nullable=True),
    sa.Column('achievement_condition_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['achievement_condition_id'], ['achievement_condition.id'], ),
    sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], )
    )
    op.create_table('completed_achievements',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('achievement_condition_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['achievement_condition_id'], ['achievement_condition.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('player_achievement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('achievement_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('player_achievement')
    op.drop_table('completed_achievements')
    op.drop_table('achievement_properties')
    op.drop_table('achievement_condition')
    op.drop_table('achievement')
    # ### end Alembic commands ###