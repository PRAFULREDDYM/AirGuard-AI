"""initial_schema

Revision ID: b9ee59aedd6b
Revises: 
Create Date: 2026-11-05 01:19:35.254340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9ee59aedd6b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(table_name)


def upgrade() -> None:
    # 1. users
    if not table_exists('users'):
        op.create_table(
            'users',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 2. homes
    if not table_exists('homes'):
        op.create_table(
            'homes',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('owner_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('address', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 3. rooms
    if not table_exists('rooms'):
        op.create_table(
            'rooms',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('room_type', sa.String(length=50), nullable=True, server_default='living_room'),
            sa.Column('floor', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('target_pm25', sa.Float(), nullable=True, server_default='12.0'),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 4. devices
    if not table_exists('devices'):
        op.create_table(
            'devices',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
            sa.Column('room_id', sa.String(length=36), sa.ForeignKey('rooms.id'), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('manufacturer', sa.String(length=255), nullable=True),
            sa.Column('model', sa.String(length=255), nullable=True),
            sa.Column('firmware_version', sa.String(length=50), nullable=True),
            sa.Column('connection_protocol', sa.String(length=50), nullable=False),
            sa.Column('is_controllable', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('is_online', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 5. device_capabilities
    if not table_exists('device_capabilities'):
        op.create_table(
            'device_capabilities',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=False, unique=True),
            sa.Column('measurements', sa.JSON(), nullable=True),
            sa.Column('controls', sa.JSON(), nullable=True),
            sa.Column('polling_interval_seconds', sa.Integer(), nullable=True, server_default='10'),
            sa.Column('supports_streaming', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('calibration_status', sa.String(length=50), nullable=True, server_default='CALIBRATED')
        )

    # 6. connections
    if not table_exists('connections'):
        op.create_table(
            'connections',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('encrypted_credentials', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('last_sync_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 7. sensor_readings
    if not table_exists('sensor_readings'):
        op.create_table(
            'sensor_readings',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=False, index=True),
            sa.Column('sensor_id', sa.String(length=100), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
            sa.Column('measurement_type', sa.String(length=50), nullable=False, index=True),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('unit', sa.String(length=30), nullable=False),
            sa.Column('provenance', sa.String(length=50), nullable=False),
            sa.Column('raw_value', sa.Float(), nullable=True),
            sa.Column('calibration_quality', sa.String(length=50), nullable=True),
            sa.Column('source_integration', sa.String(length=50), nullable=False),
            sa.Column('ingestion_timestamp', sa.DateTime(), nullable=True, index=True)
        )

    # 8. environmental_events
    if not table_exists('environmental_events'):
        op.create_table(
            'environmental_events',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('room_id', sa.String(length=36), sa.ForeignKey('rooms.id'), nullable=True),
            sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=True),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('anomaly_score', sa.Float(), nullable=True),
            sa.Column('classification', sa.String(length=100), nullable=True),
            sa.Column('classification_confidence', sa.Float(), nullable=True),
            sa.Column('model_version_id', sa.String(length=36), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('user_feedback', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 9. alerts
    if not table_exists('alerts'):
        op.create_table(
            'alerts',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
            sa.Column('event_id', sa.String(length=36), sa.ForeignKey('environmental_events.id'), nullable=True),
            sa.Column('severity', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 10. automation_rules
    if not table_exists('automation_rules'):
        op.create_table(
            'automation_rules',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('home_id', sa.String(length=36), sa.ForeignKey('homes.id'), nullable=False),
            sa.Column('room_id', sa.String(length=36), sa.ForeignKey('rooms.id'), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('trigger_config', sa.JSON(), nullable=False),
            sa.Column('action_config', sa.JSON(), nullable=False),
            sa.Column('cooldown_seconds', sa.Integer(), nullable=True, server_default='1800'),
            sa.Column('max_executions_per_hour', sa.Integer(), nullable=True, server_default='4'),
            sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )

    # 11. automation_executions
    if not table_exists('automation_executions'):
        op.create_table(
            'automation_executions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('rule_id', sa.String(length=36), sa.ForeignKey('automation_rules.id'), nullable=False),
            sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=False),
            sa.Column('command', sa.String(length=100), nullable=False),
            sa.Column('parameters', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('triggered_at', sa.DateTime(), nullable=True)
        )

    # 12. data_collection_sessions
    if not table_exists('data_collection_sessions'):
        op.create_table(
            'data_collection_sessions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('device_id', sa.String(length=36), sa.ForeignKey('devices.id'), nullable=False),
            sa.Column('room_id', sa.String(length=36), sa.ForeignKey('rooms.id'), nullable=True),
            sa.Column('label', sa.String(length=100), nullable=True),
            sa.Column('label_source', sa.String(length=50), nullable=True, server_default='user_manual'),
            sa.Column('environmental_conditions', sa.JSON(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('sample_count', sa.Integer(), nullable=True, server_default='0')
        )

    # 13. model_versions
    if not table_exists('model_versions'):
        op.create_table(
            'model_versions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('version', sa.String(length=50), nullable=False),
            sa.Column('model_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='TRAINED'),
            sa.Column('metrics', sa.JSON(), nullable=True),
            sa.Column('dataset_hash', sa.String(length=64), nullable=True),
            sa.Column('features_used', sa.JSON(), nullable=True),
            sa.Column('file_path', sa.String(length=255), nullable=True),
            sa.Column('training_date', sa.DateTime(), nullable=True)
        )

    # 14. audit_logs
    if not table_exists('audit_logs'):
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    for tbl in [
        'audit_logs', 'model_versions', 'data_collection_sessions',
        'automation_executions', 'automation_rules', 'alerts',
        'environmental_events', 'sensor_readings', 'connections',
        'device_capabilities', 'devices', 'rooms', 'homes', 'users'
    ]:
        if table_exists(tbl):
            op.drop_table(tbl)
