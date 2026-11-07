import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Float, Integer, DateTime, Enum, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from services.api.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class MeasurementType(str, enum.Enum):
    PM1 = "PM1"
    PM25 = "PM25"
    PM10 = "PM10"
    VOC_INDEX = "VOC_INDEX"
    VOC_RAW = "VOC_RAW"
    CO2 = "CO2"
    ECO2 = "ECO2"
    TEMPERATURE = "TEMPERATURE"
    HUMIDITY = "HUMIDITY"
    PRESSURE = "PRESSURE"
    NOX_INDEX = "NOX_INDEX"
    GAS_RESISTANCE = "GAS_RESISTANCE"
    AQI = "AQI"
    IAQ = "IAQ"

class DataProvenance(str, enum.Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    IMPORTED = "IMPORTED"

class CalibrationQuality(str, enum.Enum):
    UNCALIBRATED = "UNCALIBRATED"
    WARMING_UP = "WARMING_UP"
    CALIBRATED = "CALIBRATED"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

class EventSeverity(str, enum.Enum):
    INFO = "INFO"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    ANOMALY = "ANOMALY"
    WARNING = "WARNING"
    CERTIFIED_ALARM = "CERTIFIED_ALARM"

class IntegrationType(str, enum.Enum):
    HOME_ASSISTANT = "home_assistant"
    MQTT = "mqtt"
    AIRGRADIENT = "airgradient"
    ESPHOME = "esphome"
    REST = "rest"
    SIMULATION = "simulation"

# --- Tables ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    homes = relationship("Home", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan")

class Home(Base):
    __tablename__ = "homes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    address = Column(String(255), nullable=True)
    automations_paused = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="homes")
    rooms = relationship("Room", back_populates="home", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="home", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="home", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="home", cascade="all, delete-orphan")
    consents = relationship("UserConsent", back_populates="home", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="home", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False)
    name = Column(String(255), nullable=False)
    room_type = Column(String(50), default="living_room")  # living_room, kitchen, bedroom, etc.
    floor = Column(Integer, default=1)
    target_pm25 = Column(Float, default=12.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    home = relationship("Home", back_populates="rooms")
    devices = relationship("Device", back_populates="room")
    events = relationship("EnvironmentalEvent", back_populates="room")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    connection_protocol = Column(Enum(IntegrationType), nullable=False)
    is_controllable = Column(Boolean, default=False)
    is_online = Column(Boolean, default=True)
    automation_authorized = Column(Boolean, default=False)  # User permission for automation
    manual_override = Column(Boolean, default=False)
    manual_override_until = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    home = relationship("Home", back_populates="devices")
    room = relationship("Room", back_populates="devices")
    capabilities = relationship("DeviceCapability", back_populates="device", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")

class DeviceCapability(Base):
    __tablename__ = "device_capabilities"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, unique=True)
    measurements = Column(JSON, default=list)  # list of supported measurement types and units
    controls = Column(JSON, default=list)      # list of supported commands (e.g. set_speed, turn_on)
    polling_interval_seconds = Column(Integer, default=10)
    supports_streaming = Column(Boolean, default=False)
    calibration_status = Column(Enum(CalibrationQuality), default=CalibrationQuality.CALIBRATED)
    
    device = relationship("Device", back_populates="capabilities")

class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False)
    provider = Column(Enum(IntegrationType), nullable=False)
    name = Column(String(255), nullable=False)
    encrypted_credentials = Column(Text, nullable=False)  # AES-GCM encrypted json
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    sensor_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    measurement_type = Column(Enum(MeasurementType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    provenance = Column(Enum(DataProvenance), nullable=False)
    raw_value = Column(Float, nullable=True)
    calibration_quality = Column(Enum(CalibrationQuality), default=CalibrationQuality.CALIBRATED)
    source_integration = Column(String(50), nullable=False)
    ingestion_timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="readings")

class EnvironmentalEvent(Base):
    __tablename__ = "environmental_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # THRESHOLD, ANOMALY, CLASSIFIED, CERTIFIED_ALARM
    severity = Column(Enum(EventSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    classification = Column(String(100), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    model_version_id = Column(String(36), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    acknowledged = Column(Boolean, default=False)
    user_feedback = Column(String(50), nullable=True)  # "accurate", "false_positive", "unknown"
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="events")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("environmental_events.id"), nullable=True)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    severity = Column(Enum(EventSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="ELEVATED_READING")  # ELEVATED_READING, OFFLINE_SENSOR, GATEWAY_DISCONNECTED, DEVICE_ERROR, ODOR_CLASSIFIED, CERTIFIED_ALARM
    delivery_channel = Column(String(50), default="IN_APP")     # IN_APP, PUSH_NOTIFICATION, EMAIL
    delivery_status = Column(String(50), default="DELIVERED")   # DELIVERED, PENDING, SUPPRESSED_QUIET_HOURS, SUPPRESSED_COOLDOWN
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    home = relationship("Home", back_populates="alerts")

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    
    # Trigger Config (JSON)
    # { "measurement_type": "PM25", "condition": "ABOVE", "threshold": 35.0, "duration_seconds": 60, "hysteresis": 5.0 }
    trigger_config = Column(JSON, nullable=False)
    
    # Action Config (JSON)
    # { "device_id": "uuid", "command": "set_speed", "parameters": { "speed": "high" } }
    action_config = Column(JSON, nullable=False)
    
    # Constraints & Rate Limits
    cooldown_seconds = Column(Integer, default=1800)
    max_executions_per_hour = Column(Integer, default=4)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    home = relationship("Home", back_populates="automation_rules")
    executions = relationship("AutomationExecution", back_populates="rule", cascade="all, delete-orphan")

class AutomationExecution(Base):
    __tablename__ = "automation_executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(36), ForeignKey("automation_rules.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    command = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False)  # "SUCCESS", "FAILED", "BLOCKED_BY_SAFETY", "MANUAL_OVERRIDE"
    reason = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship("AutomationRule", back_populates="executions")

class DataCollectionSession(Base):
    __tablename__ = "data_collection_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    label = Column(String(100), nullable=True)  # e.g., "coffee", "cooking", "baseline"
    label_source = Column(String(50), default="user_manual")
    environmental_conditions = Column(JSON, default=dict)  # {"temp": 22.5, "humidity": 45.0}
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    sample_count = Column(Integer, default=0)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # "ANOMALY_DETECTOR", "SENSOR_CLASSIFIER", "MOLECULAR_ODOR"
    status = Column(String(50), default="TRAINED")   # "UNTRAINED", "TRAINED", "APPROVED", "DEPLOYED", "RETIRED"
    metrics = Column(JSON, default=dict)             # {"accuracy": 0.92, "f1_macro": 0.89, ...}
    dataset_hash = Column(String(64), nullable=True)
    features_used = Column(JSON, default=list)
    file_path = Column(String(255), nullable=True)
    training_date = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # AUTH_LOGIN, DEVICE_COMMAND, RULE_CHANGE, DATA_EXPORT
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

class UserConsent(Base):
    __tablename__ = "user_consents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=True, index=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True, index=True)
    integration_scope = Column(String(100), nullable=True)
    permission_type = Column(String(50), nullable=False, index=True)  # TELEMETRY_ACCESS, DEVICE_CONTROL, PUSH_NOTIFICATIONS, CLOUD_PROCESSING, AI_TRAINING_SHARE
    authorized_actions = Column(JSON, default=list)                   # ["fan.set_speed", "fan.turn_on", "fan.turn_off"]
    consent_version = Column(String(20), default="1.0")
    consent_origin = Column(String(100), default="onboarding_wizard")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="consents")
    home = relationship("Home", back_populates="consents")
    device = relationship("Device")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    home_id = Column(String(36), ForeignKey("homes.id"), nullable=False, index=True)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    event_category = Column(String(50), nullable=False)                # ELEVATED_READING, OFFLINE_SENSOR, GATEWAY_DISCONNECTED, DEVICE_ERROR, ODOR_CLASSIFIED, CERTIFIED_ALARM
    delivery_channel = Column(String(50), default="IN_APP")            # IN_APP, PUSH_NOTIFICATION, EMAIL
    enabled = Column(Boolean, default=True)
    min_severity = Column(String(50), default="ELEVATED")
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="07:00")
    cooldown_minutes = Column(Integer, default=15)
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notification_preferences")
    home = relationship("Home", back_populates="notification_preferences")
