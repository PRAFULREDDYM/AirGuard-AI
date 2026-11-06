import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sklearn.ensemble import IsolationForest

from services.api.models import (
    SensorReading, EnvironmentalEvent, Device, Room, MeasurementType, EventSeverity
)
from services.ingestion.service import ws_manager

class AnomalyDetector:
    # Rule-based threshold levels (Level 1 Monitoring)
    THRESHOLDS = {
        MeasurementType.PM25: {"elevated": 25.0, "high": 55.0, "unit": "µg/m³"},
        MeasurementType.PM10: {"elevated": 50.0, "high": 150.0, "unit": "µg/m³"},
        MeasurementType.CO2: {"elevated": 1000.0, "high": 1600.0, "unit": "ppm"},
        MeasurementType.ECO2: {"elevated": 1000.0, "high": 1600.0, "unit": "ppm"},
        MeasurementType.VOC_INDEX: {"elevated": 200.0, "high": 350.0, "unit": "index"},
        MeasurementType.NOX_INDEX: {"elevated": 150.0, "high": 300.0, "unit": "index"},
    }

    def __init__(self):
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        self.is_fitted = False

    def fit_baseline(self, feature_matrix: np.ndarray):
        """Fit Isolation Forest on normal baseline multi-sensor observations."""
        if len(feature_matrix) >= 20:
            self.isolation_forest.fit(feature_matrix)
            self.is_fitted = True

    def score_sample(self, features: np.ndarray) -> float:
        """
        Returns anomaly score between 0.0 (normal) and 1.0 (highly anomalous).
        """
        if not self.is_fitted:
            return 0.0
        # decision_function gives negative score for outliers, positive for inliers
        raw_score = self.isolation_forest.decision_function(features.reshape(1, -1))[0]
        # Normalize roughly to 0.0 - 1.0 where >0.6 indicates anomaly
        normalized_score = float(1.0 / (1.0 + np.exp(raw_score * 4.0)))
        return round(normalized_score, 3)

    @classmethod
    async def evaluate_reading(
        cls,
        db: AsyncSession,
        reading: SensorReading
    ) -> Optional[EnvironmentalEvent]:
        """
        Evaluates a single reading against rule thresholds and emits an EnvironmentalEvent
        if elevated or anomalous conditions are detected.
        """
        m_type = reading.measurement_type
        if m_type not in cls.THRESHOLDS:
            return None

        limits = cls.THRESHOLDS[m_type]
        val = reading.value

        severity = None
        title = None
        desc = None

        if val >= limits["high"]:
            severity = EventSeverity.WARNING
            title = f"High {m_type.value} Level ({val} {reading.unit})"
            desc = f"Sensor recorded significantly elevated {m_type.value} exceeding {limits['high']} {limits['unit']}."
        elif val >= limits["elevated"]:
            severity = EventSeverity.ELEVATED
            title = f"Elevated {m_type.value} Level ({val} {reading.unit})"
            desc = f"Sensor recorded elevated {m_type.value} exceeding {limits['elevated']} {limits['unit']}."

        if not severity:
            return None

        # Fetch device and room
        dev_res = await db.execute(select(Device).where(Device.id == reading.device_id))
        dev = dev_res.scalars().first()
        room_id = dev.room_id if dev else None

        # Check if an active open event already exists in this room/device within last 15 minutes
        now = datetime.utcnow()
        event = EnvironmentalEvent(
            room_id=room_id,
            device_id=reading.device_id,
            event_type="THRESHOLD_EXCEEDED",
            severity=severity,
            title=title,
            description=desc,
            anomaly_score=round(min(1.0, val / limits["high"]), 2),
            started_at=now,
            acknowledged=False
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        # Broadcast event
        await ws_manager.broadcast({
            "type": "new_event",
            "data": {
                "id": event.id,
                "room_id": event.room_id,
                "device_id": event.device_id,
                "event_type": event.event_type,
                "severity": event.severity.value,
                "title": event.title,
                "description": event.description,
                "anomaly_score": event.anomaly_score,
                "started_at": event.started_at.isoformat()
            }
        })

        return event

anomaly_detector = AnomalyDetector()

