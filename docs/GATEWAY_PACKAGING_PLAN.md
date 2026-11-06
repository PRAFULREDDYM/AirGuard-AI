# AirGuard AI — Local Gateway Distribution & Packaging Plan (Phase 7)

## 1. Problem Statement & Architecture

A web browser executing clientside JavaScript within a browser sandbox cannot:
- Listen on low-level mDNS/SSDP multicast sockets (`224.0.0.251:5353`, `239.255.255.250:1900`).
- Perform raw TCP/UDP socket scans to identify unconfigured IoT devices.
- Run continuous 24/7 background telemetry ingestion when the browser tab is closed or a laptop enters sleep.

To deliver a genuine zero-configuration consumer experience, the AirGuard Local Discovery Gateway must be easily packaged and distributed as an always-on background service across major consumer operating systems.

---

## 2. Platform-Specific Packaging Strategies

### 2.1 macOS: Menubar Runner & LaunchAgent

#### Architecture
- **Distribution format:** Universal `.dmg` containing a lightweight Swift/Cocoa menubar application (`AirGuardGateway.app`).
- **Background Daemon:** Managed via `~/Library/LaunchAgents/com.airguard.gateway.plist`.
- **Permissions:** Requests local network access entitlement (`com.apple.developer.networking.multipeer` / `NSLocalNetworkUsageDescription`).
- **Sleep Prevention:** Leverages `IOPMAssertionCreateWithName(kIOPMAssertPreventUserIdleSystemSleep)` when active real-time air automation rules are enabled, preventing automation interruption during sleep.

#### Sample LaunchAgent Plist (`com.airguard.gateway.plist`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.airguard.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/AirGuard.app/Contents/MacOS/airguard-gateway</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>NetworkState</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>/Library/Logs/AirGuard/gateway.log</string>
    <key>StandardErrorPath</key>
    <string>/Library/Logs/AirGuard/gateway.err</string>
</dict>
</plist>
```

---

### 2.2 Windows: Windows Service & System Tray

#### Architecture
- **Distribution format:** WiX-based MSI installer (`AirGuardSetup.msi`).
- **Background Service:** Managed via Windows Service Control Manager (`sc.exe create AirGuardGateway`).
- **System Tray Companion:** Minimal WPF / WinUI 3 tray icon indicating local gateway health, active IP addresses, and pairing status.
- **Firewall Rule:** MSI installer registers a Windows Defender Firewall rule allowlisting inbound mDNS (`UDP 5353`) and localhost REST communication (`TCP 8000`).

---

### 2.3 Linux & Raspberry Pi: Dedicated Systemd Unit

#### Architecture
- **Target Environments:** Dedicated home servers, Raspberry Pi 4/5, Home Assistant Yellow/Green.
- **Distribution format:** Debian package (`.deb`) and Docker image (`ghcr.io/airguard-ai/gateway:latest`).
- **Systemd Service:** `airguard-gateway.service` enabled on boot with automatic restart on network failure.

#### Sample Systemd Unit (`airguard-gateway.service`)
```ini
[Unit]
Description=AirGuard AI Local Discovery Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=airguard
Group=airguard
WorkingDirectory=/opt/airguard
ExecStart=/opt/airguard/.venv/bin/python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5s
Environment=ENVIRONMENT=production
EnvironmentFile=/etc/airguard/gateway.env

# Hardening
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/lib/airguard /var/log/airguard
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

---

### 2.4 Home Assistant Add-on Option

#### Architecture
For households already running Home Assistant OS:
- **Distribution format:** Official Home Assistant Community Add-on.
- **Configuration:** One-click install from the AirGuard Add-on Repository.
- **Communication:** Connects directly via internal Docker network (`http://supervisor/core/api`) using the Supervisor token, completely eliminating external token generation or IP configuration for the user.
- **Zero Configuration:** Automatically imports all existing Home Assistant environmental sensors and purifiers upon first launch.

---

## 3. Deployment Checklist for Release

1. **Sign & Notarize Binaries:** Code sign macOS `.app` with Developer ID Application certificate and notarize via Apple notarytool.
2. **Windows Authenticode:** Sign MSI installer and executable with an EV Code Signing certificate.
3. **Local Certificate Authority (mTLS):** Generate a local ephemeral self-signed CA on first boot to secure localhost HTTPS traffic between web UI and gateway without browser security warnings.
4. **Auto-Updater:** Integrate Sparkle (macOS) and WinSparkle (Windows) for seamless zero-click background security updates.
