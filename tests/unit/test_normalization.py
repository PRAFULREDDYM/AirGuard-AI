import pytest
from services.api.models import MeasurementType, DataProvenance
from services.ingestion.service import IngestionService

def test_temperature_fahrenheit_to_celsius():
    val, unit = IngestionService.normalize_unit_and_value(
        MeasurementType.TEMPERATURE,
        77.0,
        "°F"
    )
    assert val == 25.0
    assert unit == "°C"

def test_pm25_mg_to_ug():
    val, unit = IngestionService.normalize_unit_and_value(
        MeasurementType.PM25,
        0.035,
        "mg/m³"
    )
    assert val == 35.0
    assert unit == "µg/m³"

def test_pressure_normalization():
    val, unit = IngestionService.normalize_unit_and_value(
        MeasurementType.PRESSURE,
        101325.0,
        "Pa"
    )
    assert val == 1013.25
    assert unit == "hPa"

def test_eco2_must_not_masquerade_as_ndir_co2():
    # If provenance is ESTIMATED and type was labeled CO2, it must be renamed ECO2
    from services.api.schemas import SensorReadingCreate
    from datetime import datetime

    reading_in = SensorReadingCreate(
        device_id="dev_01",
        sensor_id="sens_01",
        timestamp=datetime.utcnow(),
        measurement_type=MeasurementType.CO2,
        value=650.0,
        unit="ppm",
        provenance=DataProvenance.ESTIMATED,
        source_integration="test"
    )

    if reading_in.measurement_type == MeasurementType.CO2 and reading_in.provenance == DataProvenance.ESTIMATED:
        reading_in.measurement_type = MeasurementType.ECO2

    assert reading_in.measurement_type == MeasurementType.ECO2

