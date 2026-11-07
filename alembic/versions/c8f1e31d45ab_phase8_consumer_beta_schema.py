"""phase8_consumer_beta_schema

Revision ID: c8f1e31d45ab
Revises: b9ee59aedd6b
Create Date: 2026-11-06 22:50:00.000000

Adds:
- user_consents table
- notification_preferences table
- push_subscriptions table
- homes.automations_paused
- devices.automation_authorized, manual_override, manual_override_until
- alerts category, delivery_channel, delivery_status, delivery_attempts, failure_reason, acknowledged_at, read_at, room_id, device_id
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8f1e31d45ab'
down_revision: Union[str, Sequence[str], None] = 'b9ee59aedd6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update homes table
    op.add_column('homes', sa.Column('automations_paused', sa.Boolean(), nullable=True, server_default=sa.text('0')))

    # 2. Update devices table
    op.add_column('devices', sa.Column('automation_authorized', sa.Boolean(), nullable=True, server_default=sa.text('0')))
    op.add_column('devices', sa.Column('manual_override', sa.Boolean(), nullable=True, server_default=sa.text('0')))
    op.add_column('devices', sa.Column('manual_override_until', sa.DateTime(), nullable=True))

    # 3. Update alerts table
    op.add_column('alerts', sa.Column('room_id', sa.String(length=36), nullable=True))
    op.add_column('alerts', sa.Column('device_id', sa.String(length=36), nullable=True))
    op.add_column('alerts', sa.Column('category', sa.String(length=50), nullable=True, server_default='ELEVATED_READING'))
    op.add_column('alerts', sa.Column('delivery_channel', sa.String(length=50), nullable=True, server_default='IN_APP'))
    op.add_column('alerts', sa.Column('delivery_status', sa.String(length=50), nullable=True, server_default='DELIVERED'))
    op.add_column('alerts', sa.Column('delivery_attempts', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('alerts', sa.Column('failure_reason', sa.Text(), nullable=True))
    op.add_column('alerts', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
    op.add_column('alerts', sa.Column('read_at', sa.DateTime(), nullable=True))

    # 4. Create user_consents table
    op.create_table(
        'user_consents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=True),
        sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('integration_scope', sa.String(length=100), nullable=True),
        sa.Column('permission_type', sa.String(length=50), nullable=False),
        sa.Column('authorized_actions', sa.JSON(), nullable=True),
        sa.Column('consent_version', sa.String(length=20), nullable=True, server_default='1.0'),
        sa.Column('consent_origin', sa.String(length=100), nullable=True, server_default='onboarding_wizard'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True)
    )

    # 5. Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
        sa.Column('room_id', sa.String(length=36), sa.ForeignKey('rooms.id'), nullable=True),
        sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('delivery_channel', sa.String(length=50), nullable=True, server_default='IN_APP'),
        sa.Column('enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('min_severity', sa.String(length=50), nullable=True, server_default='ELEVATED'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True, server_default='22:00'),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True, server_default='07:00'),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True, server_default='15'),
        sa.Column('last_notified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 6. Create push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False, unique=True),
        sa.Column('p256dh_key', sa.String(length=255), nullable=False),
        sa.Column('auth_key', sa.String(length=255), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('push_subscriptions')
    op.drop_table('notification_preferences')
    op.drop_table('user_consents')

    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.drop_column('read_at')
        batch_op.drop_column('acknowledged_at')
        batch_op.drop_column('failure_reason')
        batch_op.drop_column('delivery_attempts')
        batch_op.drop_column('delivery_status')
        batch_op.drop_column('delivery_channel')
        batch_op.drop_column('category')
        batch_op.drop_column('device_id')
        batch_op.drop_column('room_id')

    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.drop_column('manual_override_until')
        batch_op.drop_column('manual_override')
        batch_op.drop_column('automation_authorized')

    with op.batch_alter_table('homes', schema=None) as batch_op:
        batch_op.drop_column('automations_paused')
