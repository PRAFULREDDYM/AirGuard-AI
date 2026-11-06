---
name: integration-testing
description: >-
  Guide for API tests, simulated sensors, MQTT fixtures, device mock servers,
  end-to-end tests, CI pipeline configuration, and test data management.
---

# Integration Testing Skill

## Test Framework

- **Python backend:** pytest + pytest-asyncio + httpx (async test client)
- **Frontend:** Jest + React Testing Library (unit), Playwright (E2E)
- **Mock servers:** pytest fixtures with aiohttp/FastAPI test servers
- **MQTT testing:** Local mosquitto or in-memory broker fixture
- **Database:** Test PostgreSQL database or SQLite for unit tests

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- Data normalization functions
- Pydantic model validation
- Automation rule evaluation
- Safety policy checks
- Unit conversion
- Measurement type validation

### 2. Integration Tests (`tests/integration/`)
- API endpoint behavior (CRUD operations)
- Database persistence and queries
- Adapter connection/disconnection
- MQTT message processing
- WebSocket event delivery
- Model training pipeline (with sample data)

### 3. End-to-End Tests (`tests/e2e/`)
- User onboarding flow
- Device pairing wizard
- Dashboard real-time updates
- Automation creation and execution
- Model training workflow
- Settings management

## Mock Server Patterns

### Home Assistant Mock
```python
@pytest.fixture
async def mock_ha_server():
    """Fake Home Assistant API with sensor entities."""
    # Returns test entities: sensor.pm25, fan.purifier, etc.
    # Validates auth tokens
    # Accepts service calls
```

### MQTT Fixture
```python
@pytest.fixture
async def mqtt_broker():
    """In-process MQTT broker for testing."""
    # Starts a test broker
    # Provides publish/subscribe helpers
    # Cleans up after test
```

## Required Test Scenarios

1. ✅ Application starts and health check passes
2. ✅ Database migrations complete without errors
3. ✅ User can create home and rooms
4. ✅ Simulated sensor data ingestion works
5. ✅ Real adapter connection test (with mock server)
6. ✅ Malformed sensor data is rejected with proper error
7. ✅ Stale sensor detection works
8. ✅ Anomaly detection produces events
9. ✅ Untrained classifier returns "not trained"
10. ✅ Automation issues commands to mock device
11. ✅ Manual override prevents automation
12. ✅ Unsafe automation is blocked (gas leak + fan)
13. ✅ Cross-user data access is denied
14. ✅ Rate limiting works

## Validation Checklist

- [ ] Tests run without real hardware or credentials
- [ ] Each test is independent (no shared state)
- [ ] Mock servers validate auth like real services
- [ ] Database is cleaned between tests
- [ ] Tests clearly document what requires real hardware
- [ ] CI pipeline runs all tests on every commit
- [ ] Test coverage reported

