# AirGuard AI — Security & Safety Design

## Authentication Architecture

### User Authentication
- JWT-based with short-lived access tokens (15 min) and refresh tokens (7 days)
- Passwords hashed with bcrypt (cost factor 12)
- HttpOnly, Secure, SameSite=Strict cookies for web sessions
- Rate-limited login attempts (5/min per IP)

### Integration Credentials
- Encrypted at rest with AES-256-GCM
- Encryption key from environment variable `AIRGUARD_ENCRYPTION_KEY`
- Never returned in API responses (write-only)
- Rotatable without service restart

## Authorization Model

```
User → owns → Home(s) → contains → Room(s) → has → Device(s)
```

Every API request is scoped to the authenticated user's homes. Cross-user access is denied at the query layer.

Device control requires explicit per-device automation permission from the user.

## Safety Decision Matrix

| Condition | ML Says | Action | Rationale |
|-----------|---------|--------|-----------|
| Smoke alarm fires | Anything | Emergency alert, DO NOT control HVAC | Fire safety |
| CO alarm fires | Anything | Emergency alert, DO NOT control devices | CO safety |
| Gas leak suspected | Anything | Warning, DO NOT activate electrical | Ignition risk |
| PM2.5 elevated | Anomaly | Alert + optional purifier automation | Safe action |
| VOC elevated | Anomaly | Alert + ventilation recommendation | Recommendation only |
| Unknown event | Unknown | Alert, log, ask user | Cannot assume safety |
| Model untrained | N/A | Report "not trained" | Honesty |

## Network Security

- API accessible only on configured interfaces
- CORS restricted to frontend origin
- CSP headers prevent XSS
- No unrestricted proxy to local network devices
- Device adapter connections validated before saving
- MQTT topic validation prevents injection

## Audit Trail

Events logged:
1. User authentication (login/logout/failure)
2. Device control commands (what, when, who, result)
3. Automation rule changes
4. Credential operations
5. Data export/deletion
6. Model deployment/rollback

## Data Privacy

- All sensor data stays local by default
- User can export all data (JSON/CSV)
- User can delete account and all data
- Configurable retention periods (default: 90 days for readings, 1 year for events)
- No third-party analytics without opt-in

