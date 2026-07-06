"""create booking_payments table

Revision ID: c31f2a9d8e10
Revises: 467dc3b557f4
Create Date: 2026-07-05 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c31f2a9d8e10'
down_revision = '467dc3b557f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'booking_payments',
        sa.Column('payment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('booking_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('booking_payment_date', sa.DateTime(), nullable=False),
        sa.Column('booking_payment_status', sa.Enum('pending', 'paid', 'failed', 'cancelled', name='payment_status'), nullable=False, server_default='pending'),
        sa.Column('booking_userid', sa.Integer(), nullable=False),
        sa.Column('booking_bookingid', sa.Integer(), nullable=False),
        sa.Column('advert_payment_reference', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['booking_userid'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['booking_bookingid'], ['booking_details.booking_detail_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('payment_id'),
        sa.UniqueConstraint('advert_payment_reference')
    )
    op.create_index(op.f('ix_booking_payments_booking_payment_status'), 'booking_payments', ['booking_payment_status'], unique=False)
    op.create_index(op.f('ix_booking_payments_booking_userid'), 'booking_payments', ['booking_userid'], unique=False)
    op.create_index(op.f('ix_booking_payments_booking_bookingid'), 'booking_payments', ['booking_bookingid'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_booking_payments_booking_bookingid'), table_name='booking_payments')
    op.drop_index(op.f('ix_booking_payments_booking_userid'), table_name='booking_payments')
    op.drop_index(op.f('ix_booking_payments_booking_payment_status'), table_name='booking_payments')
    op.drop_table('booking_payments')
