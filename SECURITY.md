# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

AirGuard AI handles device control actions and local network discovery. Security reports regarding potential privilege escalation, unauthorized actuation, or SSRF risks are taken seriously.

Please report security concerns responsibly via GitHub Security Advisories or by emailing the project maintainers directly rather than opening public issues.

### Invariant Defenses in Place
- Local SSRF validation on all webhook and adapter host inputs
- Atomic pre-dispatch double checks to eliminate control race conditions
- Unbundled, cryptographically signed local user consent verification
- Rate-limiting enforced at the actuation layer (max 1 command per 30s per device)

