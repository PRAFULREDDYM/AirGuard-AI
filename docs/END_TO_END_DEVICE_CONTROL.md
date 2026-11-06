# AirGuard AI — End-to-End Device Control & Safety Architecture (Phase 7)

## 1. Overview & Control Philosophy

AirGuard AI bridges environmental machine learning insights with physical smart actuators (air purifiers, ventilation fans, dampers, and air scrubbers).

Device actuation is governed by strict deterministic safety rules. **Machine learning predictions never directly trigger electrical relays without passing through the deterministic Safety Engine.**

```
+-------------------------------------------------------------+
|               AirGuard Environmental Monitoring             |
|   (Laser PM2.5, NDIR CO2, VOC Index, BME688 MOX Timeseries) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|            Environmental ML & Anomaly Detection             |
|      (Isolation Forest, Baseline Tracking, Odor Class)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             Automation Engine Rule Evaluation               |
|      (Clean Air Guard, Odor Eliminator, Night Quiet)        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             DETERMINISTIC SAFETY ENGINE CHECK               |
|  - Life-Safety Hazard Check (Fire, Smoke, Combustible Gas)  |
|  - Manual Override Verification                             |
|  - User Automation Permission Check                         |
|  - Actuator Capability Manifest Validation                  |
|  - Rate-Limiting & Cooldown Protection                      |
+-------------------------------------------------------------+
                              |
                +-------------+-------------+
                |                           |
             [PASSED]                    [BLOCKED]
                |                           |
                v                           v
+---------------------------------+  +-------------------------------+
|      Adapter Command Dispatch   |  | Safety Violation / Suspended  |
| (Home Assistant / Local miIO)   |  | - Set EMERGENCY_SUSPENDED     |
|                                 |  | - Alert User Immediately      |
|  - Send Actuation Command       |  | - Suppress Actuation          |
|  - Await Physical ACK           |  | - Write to AuditLog           |
|  - Verify Telemetry Response    |  +-------------------------------+
|  - Log Action to Audit Trail    |
+---------------------------------+
```

---

## 2. Non-Negotiable Safety Policies

### 2.1 The Conservative Emergency Suspended State (`EMERGENCY_SUSPENDED`)
In legacy automation scripts, a common naive mistake was attempting to command fans or electrical switches "OFF" during fire or gas leak detections.

**Why this is dangerous:**
1. **Ignition Spark Hazard:** Actuating an electrical mechanical relay or electronic switch OFF in the presence of explosive gases (methane, propane, LPG, hydrogen) can produce an internal electrical contact arc, risking ignition of the gas mixture.
2. **Interference with Certified Smoke Systems:** In a building fire, dedicated smoke evacuation systems or fire dampers may be operating under certified building code controllers. Random home automation signals commanding ventilation off can disrupt life-safety air handling.

**AirGuard Policy:**
Upon detection of combustible gas, fire, smoke, or certified safety alarm activation, the Safety Engine enters **`EMERGENCY_SUSPENDED`**.
- All ordinary automated switching is halted immediately.
- Electrical relays and purifiers remain unactuated by AirGuard.
- High-priority emergency alerts are presented to the user with evacuation and emergency guidance.

### 2.2 Direct Ozone Generator Prohibition
Ozone ($O_3$) is a potent lung irritant and hazardous air pollutant. AirGuard strictly rejects any device or command claiming to generate ozone, ionize air with ozone byproducts, or "shock-treat" inhabited rooms.

### 2.3 Strict Separation of Actuation and Sensing
Monitoring devices (such as AirGradient ONE, Awair Element, PurpleAir, and raw sensor nodes) are classified as **Read-Only Sensor Stations**. Any attempt to route actuation commands to a read-only monitoring station is rejected at the API boundary with `400 Bad Request`.

---

## 3. Command Lifecycle & State Transitions

1. **Initiation:** Triggered by an Automation Rule (e.g. PM2.5 > 25 µg/m³ for 3 consecutive minutes) or direct user intervention in the UI.
2. **Multi-Tenant Ownership Verification:** The backend verifies that the device belongs to a home owned by the authenticated caller (`home.owner_id == current_user.id`). Cross-home command attempts are rejected with `403 Forbidden`.
3. **Safety Engine Evaluation:**
   - Checks `device.manual_override`. If true, automated commands are discarded.
   - Checks `device.automation_authorized`. If false, automated dispatch is blocked.
   - Validates command against `device.capabilities.controls`.
4. **Adapter Dispatch & Acknowledgment:**
   - Command formatted and transmitted to target device adapter (Home Assistant REST, Direct Local, or Simulation).
   - Awaits synchronous physical acknowledgment (e.g. HTTP 200 / miIO `ack`).
5. **Cooldown & Rate-Limiting:**
   - Enforces a minimum 30-second hardware cooldown between successive commands to prevent motor stress and oscillation.
6. **Audit Trail Persistence:**
   - Every actuation event is recorded to the immutable `audit_logs` table with user ID, target device ID, command parameters, and execution response.
