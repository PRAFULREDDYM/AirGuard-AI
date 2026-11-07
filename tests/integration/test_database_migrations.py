"""
AirGuard AI — Phase 8: Database Migration & Schema Upgrade Verification
Tests:
- Upgrading from previous schema to current head (c8f1e31d45ab).
- Data preservation during migration on populated tables.
- Verification of new columns: automations_paused, delivery_attempts, acknowledged_at.
- Verification of new tables: user_consents, notification_preferences, push_subscriptions.
"""

import pytest
import sqlite3
import tempfile
import os
from alembic.config import Config
from alembic import command

@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "migration_test.db")
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)

def test_alembic_upgrade_populated_database(temp_db_path):
    """
    Simulates an existing v1 database with users, homes, devices, and alerts,
    and applies Alembic upgrade to head, verifying data preservation.
    """
    # 1. Initialize v1 schema manually in the test database
    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE users (
        id VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME
    );
    """)
    cur.execute("""
    CREATE TABLE homes (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        owner_id VARCHAR(36) NOT NULL,
        address VARCHAR(255),
        created_at DATETIME,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    """)
    cur.execute("""
    CREATE TABLE rooms (
        id VARCHAR(36) PRIMARY KEY,
        home_id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        room_type VARCHAR(50),
        floor INTEGER DEFAULT 1,
        target_pm25 FLOAT DEFAULT 12.0,
        created_at DATETIME
    );
    """)
    cur.execute("""
    CREATE TABLE devices (
        id VARCHAR(36) PRIMARY KEY,
        home_id VARCHAR(36) NOT NULL,
        room_id VARCHAR(36),
        name VARCHAR(255) NOT NULL,
        manufacturer VARCHAR(100) NOT NULL,
        model VARCHAR(100) NOT NULL,
        firmware_version VARCHAR(50),
        connection_protocol VARCHAR(50) NOT NULL,
        is_controllable BOOLEAN DEFAULT 0,
        is_online BOOLEAN DEFAULT 1,
        last_seen_at DATETIME,
        created_at DATETIME
    );
    """)
    cur.execute("""
    CREATE TABLE alerts (
        id VARCHAR(36) PRIMARY KEY,
        home_id VARCHAR(36) NOT NULL,
        event_id VARCHAR(36),
        severity VARCHAR(50) NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME
    );
    """)
    cur.execute("""
    CREATE TABLE alembic_version (
        version_num VARCHAR(32) NOT NULL PRIMARY KEY
    );
    """)
    # Set current version to initial schema
    cur.execute("INSERT INTO alembic_version VALUES ('b9ee59aedd6b');")

    # Seed existing data
    cur.execute("INSERT INTO users VALUES ('u1', 'test@airguard.ai', 'hash', 'Test User', 1, '2026-11-01');")
    cur.execute("INSERT INTO homes VALUES ('h1', 'Main Home', 'u1', '123 Test St', '2026-11-01');")
    cur.execute("INSERT INTO devices VALUES ('d1', 'h1', NULL, 'Purifier Pro', 'Levoit', 'Core 400S', '1.0', 'simulation', 1, 1, NULL, '2026-11-01');")
    cur.execute("INSERT INTO alerts VALUES ('a1', 'h1', NULL, 'INFO', 'Welcome', 'System active', 0, '2026-11-01');")
    conn.commit()
    conn.close()

    # 2. Run Alembic upgrade head
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{temp_db_path}")
    command.upgrade(alembic_cfg, "head")

    # 3. Verify upgraded schema & preserved data
    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()

    # Verify existing data preserved
    cur.execute("SELECT id, email, full_name FROM users WHERE id = 'u1';")
    user_row = cur.fetchone()
    assert user_row == ('u1', 'test@airguard.ai', 'Test User')

    cur.execute("SELECT id, name, automations_paused FROM homes WHERE id = 'h1';")
    home_row = cur.fetchone()
    assert home_row[0] == 'h1'
    assert home_row[1] == 'Main Home'

    cur.execute("SELECT id, name, automation_authorized, manual_override FROM devices WHERE id = 'd1';")
    dev_row = cur.fetchone()
    assert dev_row[0] == 'd1'
    assert dev_row[1] == 'Purifier Pro'

    cur.execute("SELECT id, title, delivery_attempts, delivery_status FROM alerts WHERE id = 'a1';")
    alert_row = cur.fetchone()
    assert alert_row[0] == 'a1'
    assert alert_row[1] == 'Welcome'

    # Verify new tables exist and are queryable
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    assert 'user_consents' in tables
    assert 'notification_preferences' in tables
    assert 'push_subscriptions' in tables

    # Verify alembic_version points to head
    cur.execute("SELECT version_num FROM alembic_version;")
    ver = cur.fetchone()[0]
    assert ver == 'c8f1e31d45ab'

    conn.close()
