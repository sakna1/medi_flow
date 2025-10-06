"""Changed column in Patient table

Revision ID: 1356982d65ba
Revises: 98feeefb5abd
Create Date: 2025-10-06 00:55:25.197341
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1356982d65ba'
down_revision = '98feeefb5abd'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add column as nullable first
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.add_column(sa.Column('disease_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_patient_disease', 'disease_desc', ['disease_id'], ['id'])
        batch_op.drop_column('disease')

    # Step 2: Optionally set default for existing patients
    op.execute("UPDATE patient SET disease_id = 1 WHERE disease_id IS NULL;")  # Assuming id=1 exists

    # Step 3: Make column non-nullable after data is fixed
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.alter_column('disease_id', existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.add_column(sa.Column('disease', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.drop_constraint('fk_patient_disease', type_='foreignkey')
        batch_op.drop_column('disease_id')
