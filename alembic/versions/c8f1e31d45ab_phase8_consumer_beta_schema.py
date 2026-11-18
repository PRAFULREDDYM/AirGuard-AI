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


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(table_name)


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        columns = [c['name'] for c in insp.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def upgrade() -> None:
    # 1. Update homes table
    if table_exists('homes'):
        if not column_exists('homes', 'automations_paused'):
            op.add_column('homes', sa.Column('automations_paused', sa.Boolean(), nullable=True, server_default=sa.text('0')))

    # 2. Update devices table
    if table_exists('devices'):
        if not column_exists('devices', 'automation_authorized'):
            op.add_column('devices', sa.Column('automation_authorized', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        if not column_exists('devices', 'manual_override'):
            op.add_column('devices', sa.Column('manual_override', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        if not column_exists('devices', 'manual_override_until'):
            op.add_column('devices', sa.Column('manual_override_until', sa.DateTime(), nullable=True))

    # 3. Update alerts table
    if table_exists('alerts'):
        if not column_exists('alerts', 'room_id'):
            op.add_column('alerts', sa.Column('room_id', sa.String(length=36), nullable=True))
        if not column_exists('alerts', 'device_id'):
            op.add_column('alerts', sa.Column('device_id', sa.String(length=36), nullable=True))
        if not column_exists('alerts', 'category'):
            op.add_column('alerts', sa.Column('category', sa.String(length=50), nullable=True, server_default='ELEVATED_READING'))
        if not column_exists('alerts', 'delivery_channel'):
            op.add_column('alerts', sa.Column('delivery_channel', sa.String(length=50), nullable=True, server_default='IN_APP'))
        if not column_exists('alerts', 'delivery_status'):
            op.add_column('alerts', sa.Column('delivery_status', sa.String(length=50), nullable=True, server_default='DELIVERED'))
        if not column_exists('alerts', 'delivery_attempts'):
            op.add_column('alerts', sa.Column('delivery_attempts', sa.Integer(), nullable=True, server_default='1'))
        if not column_exists('alerts', 'failure_reason'):
            op.add_column('alerts', sa.Column('failure_reason', sa.Text(), nullable=True))
        if not column_exists('alerts', 'acknowledged_at'):
            op.add_column('alerts', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        if not column_exists('alerts', 'read_at'):
            op.add_column('alerts', sa.Column('read_at', sa.DateTime(), nullable=True))

    # 4. Create user_consents table
    if not table_exists('user_consents'):
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
    if not table_exists('notification_preferences'):
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
    if not table_exists('push_subscriptions'):
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
    if table_exists('push_subscriptions'):
        op.drop_table('push_subscriptions')
    if table_exists('notification_preferences'):
        op.drop_table('notification_preferences')
    if table_exists('user_consents'):
        op.drop_table('user_consents')

    if table_exists('alerts'):
        with op.batch_alter_table('alerts', schema=None) as batch_op:
            for col in ['read_at', 'acknowledged_at', 'failure_reason', 'delivery_attempts',
                        'delivery_status', 'delivery_channel', 'category', 'device_id', 'room_id']:
                if column_exists('alerts', col):
                    batch_op.drop_column(col)

    if table_exists('devices'):
        with op.batch_alter_table('devices', schema=None) as batch_op:
            for col in ['manual_override_until', 'manual_override', 'automation_authorized']:
                if column_exists('devices', col):
                    batch_op.drop_column(col)

    if table_exists('homes'):
        with op.batch_alter_table('homes', schema=None) as batch_op:
            if column_exists('homes', 'automations_paused'):
                batch_op.drop_column('automations_paused')
