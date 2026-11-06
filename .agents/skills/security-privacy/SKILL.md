---
name: security-privacy
description: >-
  Guide for authentication, authorization, credential management, network security,
  secret scanning, privacy controls, audit logging, and data protection.
---

# Security & Privacy Skill

## Authentication

- **Method:** JWT-based authentication with refresh tokens
- **Password storage:** bcrypt with cost factor ≥ 12
- **Session:** HttpOnly, Secure, SameSite=Strict cookies for web; Bearer tokens for API
- **Token expiry:** Access token 15 min, refresh token 7 days (configurable)

## Authorization

- **Model:** Per-home ownership. User must be a member of a home to access its data.
- **Checks:** Every API endpoint verifies user owns/has access to the requested resource
- **Device control:** Additional per-device permission (user must explicitly authorize automation)

## Credential Storage

| Credential Type | Storage Method |
|----------------|---------------|
| User passwords | bcrypt hash in DB |
| HA access tokens | AES-256 encrypted in DB, key from env var |
| MQTT credentials | AES-256 encrypted in DB |
| API keys | AES-256 encrypted in DB |
| JWT signing key | Environment variable only |

### Rules
- NEVER store plaintext tokens in browser localStorage/sessionStorage
- NEVER commit secrets to source control
- NEVER log credentials or tokens
- NEVER include credentials in API error responses
- `.env` files MUST be in `.gitignore`

## Input Validation

- All API inputs validated with Pydantic models
- SQL injection prevented by SQLAlchemy parameterized queries
- XSS prevented by React's default escaping + CSP headers
- Path traversal prevented by validating file paths
- MQTT topic injection prevented by topic validation
- Device command injection prevented by capability allowlisting

## Audit Logging

Log these events with timestamp, user, IP, and result:
- Authentication attempts (success + failure)
- Device control commands
- Automation rule changes
- Credential creation/rotation
- Data export/deletion requests
- Admin actions

## API Rate Limiting

| Endpoint Category | Limit |
|------------------|-------|
| Authentication | 5/min per IP |
| Device commands | 10/min per device |
| Sensor ingestion | 100/min per device |
| General API | 60/min per user |

## Data Privacy

- Users can export all their data (JSON/CSV)
- Users can delete their account and all associated data
- Configurable data retention periods
- No third-party analytics without explicit opt-in
- Sensor data stays local by default

## Validation Checklist

- [ ] All endpoints require authentication (except health + login)
- [ ] Home ownership verified on every data access
- [ ] Credentials encrypted at rest
- [ ] No secrets in source control (scan with git-secrets or similar)
- [ ] Rate limiting active on all endpoints
- [ ] Audit log captures security-relevant events
- [ ] CORS configured restrictively
- [ ] CSP headers set
- [ ] Data export/deletion works

