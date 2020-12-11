"""Add area column

Revision ID: 9683b9c7b361
Revises: d810a2163028
Create Date: 2020-12-11 19:01:09.721813

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9683b9c7b361'
down_revision = 'd810a2163028'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('disaster_areas', sa.Column('area', sa.Float(), nullable=True))
    op.create_index(op.f('ix_disaster_areas_area'), 'disaster_areas', ['area'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_disaster_areas_area'), table_name='disaster_areas')
    op.drop_column('disaster_areas', 'area')
    # ### end Alembic commands ###