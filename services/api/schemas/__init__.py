from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from services.api.models import (
    MeasurementType, DataProvenance, CalibrationQuality,
    EventSeverity, IntegrationType
)

# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Home & Room Schemas ---
class HomeCreate(BaseModel):
    name: str
    address: Optional[str] = None

class HomeResponse(BaseModel):
    id: str
    name: str
    address: Optional[str]
    owner_id: str
    automations_paused: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoomCreate(BaseModel):
    home_id: str
    name: str
    room_type: str = "living_room"
    floor: int = 1
    target_pm25: float = 12.0

class RoomResponse(BaseModel):
    id: str
    home_id: str
    name: str
    room_type: str
    floor: int
    target_pm25: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Device Schemas ---
class DeviceCapabilitySchema(BaseModel):
    measurements: List[Any] = []
    controls: List[Any] = []
    polling_interval_seconds: int = 10
    supports_streaming: bool = False
    calibration_status: CalibrationQuality = CalibrationQuality.CALIBRATED
    model_config = ConfigDict(from_attributes=True)

class DeviceCreate(BaseModel):
    home_id: str
    room_id: Optional[str] = None
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    connection_protocol: IntegrationType
    is_controllable: bool = False
    capabilities: Optional[DeviceCapabilitySchema] = None

class DeviceResponse(BaseModel):
    id: str
    home_id: str
    room_id: Optional[str]
    name: str
    manufacturer: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    connection_protocol: IntegrationType
    is_controllable: bool
    is_online: bool
    automation_authorized: bool
    manual_override: bool
    last_seen_at: datetime
    capabilities: Optional[DeviceCapabilitySchema] = None
    model_config = ConfigDict(from_attributes=True)

class DeviceCommandRequest(BaseModel):
    command: str  # e.g., "set_speed", "turn_on", "turn_off"
    parameters: Dict[str, Any] = {}

class DeviceCommandResult(BaseModel):
    success: bool
    message: str
    command: str
    executed_at: datetime

# --- Sensor Reading Schemas (Canonical) ---
class SensorReadingCreate(BaseModel):
    device_id: str
    sensor_id: str
    timestamp: datetime
    measurement_type: MeasurementType
    value: float
    unit: str
    provenance: DataProvenance = DataProvenance.MEASURED
    raw_value: Optional[float] = None
    calibration_quality: CalibrationQuality = CalibrationQuality.CALIBRATED
    source_integration: str

class SensorReadingResponse(BaseModel):
    id: str
    device_id: str
    sensor_id: str
    timestamp: datetime
    measurement_type: MeasurementType
    value: float
    unit: str
    provenance: DataProvenance
    raw_value: Optional[float]
    calibration_quality: CalibrationQuality
    source_integration: str
    ingestion_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Event & Alert Schemas ---
class EventResponse(BaseModel):
    id: str
    room_id: Optional[str]
    device_id: Optional[str]
    event_type: str
    severity: EventSeverity
    title: str
    description: Optional[str]
    anomaly_score: Optional[float]
    classification: Optional[str]
    classification_confidence: Optional[float]
    model_version_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    acknowledged: bool
    user_feedback: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EventAcknowledge(BaseModel):
    user_feedback: Optional[str] = None  # "accurate", "false_positive", "unknown"

class AlertResponse(BaseModel):
    id: str
    home_id: str
    event_id: Optional[str] = None
    room_id: Optional[str] = None
    device_id: Optional[str] = None
    severity: EventSeverity
    title: str
    message: str
    category: str = "ELEVATED_READING"
    delivery_channel: str = "IN_APP"
    delivery_status: str = "DELIVERED"
    delivery_attempts: int = 1
    failure_reason: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AlertAckResponse(BaseModel):
    alert_id: str
    delivery_status: str
    acknowledged_at: datetime
    message: str

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: Optional[str] = None

class PushSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    endpoint: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Automation Schemas ---
class AutomationRuleCreate(BaseModel):
    home_id: str
    room_id: Optional[str] = None
    name: str
    enabled: bool = True
    trigger_config: Dict[str, Any]
    action_config: Dict[str, Any]
    cooldown_seconds: int = 1800
    max_executions_per_hour: int = 4

class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    trigger_config: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None
    cooldown_seconds: Optional[int] = None
    max_executions_per_hour: Optional[int] = None

class AutomationRuleResponse(BaseModel):
    id: str
    home_id: str
    room_id: Optional[str]
    name: str
    enabled: bool
    trigger_config: Dict[str, Any]
    action_config: Dict[str, Any]
    cooldown_seconds: int
    max_executions_per_hour: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AutomationExecutionResponse(BaseModel):
    id: str
    rule_id: str
    device_id: str
    command: str
    parameters: Optional[Dict[str, Any]]
    status: str
    reason: Optional[str]
    triggered_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- ML Schemas ---
class SessionCreate(BaseModel):
    name: str
    device_id: str
    room_id: Optional[str] = None
    label: Optional[str] = None
    environmental_conditions: Dict[str, Any] = {}
    notes: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    name: str
    device_id: str
    room_id: Optional[str]
    label: Optional[str]
    label_source: str
    environmental_conditions: Dict[str, Any]
    notes: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    sample_count: int
    model_config = ConfigDict(from_attributes=True)

class ModelVersionResponse(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    status: str
    metrics: Dict[str, Any]
    dataset_hash: Optional[str]
    features_used: List[str]
    training_date: datetime
    model_config = ConfigDict(from_attributes=True)

class MolecularPredictRequest(BaseModel):
    smiles: str

class MolecularPredictResponse(BaseModel):
    smiles: str
    is_valid_smiles: bool
    molecular_weight: Optional[float] = None
    predicted_descriptors: List[Dict[str, Any]] = []
    model_name: str
    model_version: str
    provenance: str = "Morgan Fingerprint + Random Forest Baseline"
    warning: str = "Predicted odor descriptors are statistical predictions, NOT chemical assays or toxic hazard verifications."

# --- Connection Schemas ---
class ConnectionCreate(BaseModel):
    home_id: str
    provider: IntegrationType
    name: str
    credentials: Dict[str, Any]

class ConnectionTestRequest(BaseModel):
    provider: IntegrationType
    credentials: Dict[str, Any]

class ConnectionResponse(BaseModel):
    id: str
    home_id: str
    provider: IntegrationType
    name: str
    is_active: bool
    last_sync_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Consent & Permission Schemas ---
class ConsentCreate(BaseModel):
    home_id: Optional[str] = None
    device_id: Optional[str] = None
    integration_scope: Optional[str] = None
    permission_type: str  # TELEMETRY_ACCESS, DEVICE_CONTROL, PUSH_NOTIFICATIONS, CLOUD_PROCESSING, AI_TRAINING_SHARE
    authorized_actions: List[str] = []
    consent_version: str = "1.0"
    consent_origin: str = "onboarding_wizard"

class ConsentResponse(BaseModel):
    id: str
    user_id: str
    home_id: Optional[str]
    device_id: Optional[str]
    integration_scope: Optional[str]
    permission_type: str
    authorized_actions: List[str]
    consent_version: str
    consent_origin: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

# --- Notification Preference Schemas ---
class NotificationPreferenceCreate(BaseModel):
    home_id: str
    room_id: Optional[str] = None
    device_id: Optional[str] = None
    event_category: str  # ELEVATED_READING, OFFLINE_SENSOR, GATEWAY_DISCONNECTED, DEVICE_ERROR, ODOR_CLASSIFIED, CERTIFIED_ALARM
    delivery_channel: str = "IN_APP"
    enabled: bool = True
    min_severity: str = "ELEVATED"
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    cooldown_minutes: int = 15

class NotificationPreferenceResponse(BaseModel):
    id: str
    user_id: str
    home_id: str
    room_id: Optional[str]
    device_id: Optional[str]
    event_category: str
    delivery_channel: str
    enabled: bool
    min_severity: str
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    cooldown_minutes: int
    last_notified_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NotificationTestRequest(BaseModel):
    home_id: str
    channel: str = "IN_APP"  # IN_APP, PUSH_NOTIFICATION

# --- Onboarding Activation Schemas ---
class OnboardingActivationRequest(BaseModel):
    home_id: str
    operating_mode: str = "MONITOR_ONLY"  # MONITOR_ONLY, AUTO_CONTROL
    paired_devices: List[Dict[str, Any]] = []
    consents: List[ConsentCreate] = []
    notification_preferences: List[NotificationPreferenceCreate] = []
    purifier_rule: Optional[Dict[str, Any]] = None
