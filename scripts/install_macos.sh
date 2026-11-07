#!/usr/bin/env bash
# AirGuard AI — macOS Standalone Beta Installer
# Installs user-space local gateway runtime without sudo or root privileges.

set -e

echo "=========================================================="
echo "          AirGuard AI — macOS Beta Installer              "
echo "=========================================================="

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${HOME}/.local/share/airguard-ai"
DATA_DIR="${HOME}/.airguard"
LOG_DIR="${HOME}/Library/Logs/AirGuard"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/Applications/AirGuard AI.app"
PLIST_FILE="${HOME}/Library/LaunchAgents/ai.airguard.gateway.plist"

echo "1. Checking System Architecture & Prerequisites..."
ARCH=$(uname -m)
echo "Architecture: ${ARCH} (macOS $(sw_vers -productVersion))"

# Check Python 3.11+
PYTHON_BIN=""
if command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [ "${PY_VER}" = "3.11" ] || [ "${PY_VER}" = "3.12" ]; then
        PYTHON_BIN="python3"
    fi
fi

if [ -z "${PYTHON_BIN}" ] && [ -f "${SOURCE_DIR}/.venv/bin/python" ]; then
    PYTHON_BIN="${SOURCE_DIR}/.venv/bin/python"
fi

if [ -z "${PYTHON_BIN}" ]; then
    echo "ERROR: Python 3.11 or higher is required."
    exit 1
fi
echo "Using Python runtime: ${PYTHON_BIN}"

echo "2. Setting up target directories..."
mkdir -p "${INSTALL_DIR}" "${DATA_DIR}" "${LOG_DIR}" "${BIN_DIR}" "${HOME}/Applications" "${HOME}/Library/LaunchAgents"

echo "3. Synchronizing AirGuard application files..."
rsync -av --exclude '.git' --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
    "${SOURCE_DIR}/services" \
    "${SOURCE_DIR}/alembic" \
    "${SOURCE_DIR}/alembic.ini" \
    "${SOURCE_DIR}/models" \
    "${INSTALL_DIR}/"

# Copy or reuse virtual environment
if [ -d "${SOURCE_DIR}/.venv" ]; then
    echo "Bundling virtualenv runtime to installation directory..."
    mkdir -p "${INSTALL_DIR}/.venv"
    rsync -av "${SOURCE_DIR}/.venv/" "${INSTALL_DIR}/.venv/"
fi

# Copy airguard-ctl
cp "${SOURCE_DIR}/scripts/airguard-ctl" "${INSTALL_DIR}/airguard-ctl"
chmod +x "${INSTALL_DIR}/airguard-ctl"
ln -sf "${INSTALL_DIR}/airguard-ctl" "${BIN_DIR}/airguard-ctl"

echo "4. Preserving existing database..."
if [ -f "${DATA_DIR}/airguard.db" ]; then
    echo "Existing database detected at ${DATA_DIR}/airguard.db. Settings preserved."
else
    echo "Initializing new database configuration..."
    touch "${DATA_DIR}/airguard.db"
fi

echo "5. Installing LaunchAgent daemon (ai.airguard.gateway.plist)..."
cat << EOF > "${PLIST_FILE}"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.airguard.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/.venv/bin/uvicorn</string>
        <string>services.api.main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>${INSTALL_DIR}</string>
        <key>DATABASE_URL</key>
        <string>sqlite+aiosqlite:///${DATA_DIR}/airguard.db</string>
        <key>ENVIRONMENT</key>
        <string>production</string>
        <key>ENABLE_MOCK_PROVIDERS</key>
        <string>false</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/gateway.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/gateway_error.log</string>
</dict>
</plist>
EOF

echo "6. Creating macOS Application Launcher (${APP_DIR})..."
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

cat << 'EOF' > "${APP_DIR}/Contents/MacOS/AirGuard AI"
#!/usr/bin/env bash
# AirGuard AI Desktop Launcher
GATEWAY_URL="http://127.0.0.1:8000"
WEB_URL="http://127.0.0.1:3000"

# Check if gateway is running
if ! curl -s --max-time 1 "${GATEWAY_URL}/health" >/dev/null 2>&1; then
    "${HOME}/.local/share/airguard-ai/airguard-ctl" start
    sleep 2
fi

# Open browser to dashboard or onboarding
if curl -s --max-time 1 "${WEB_URL}" >/dev/null 2>&1; then
    open "${WEB_URL}"
else
    open "${GATEWAY_URL}/docs"
fi
EOF

chmod +x "${APP_DIR}/Contents/MacOS/AirGuard AI"

cat << EOF > "${APP_DIR}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>AirGuard AI</string>
    <key>CFBundleIdentifier</key>
    <string>ai.airguard.desktop</string>
    <key>CFBundleName</key>
    <string>AirGuard AI</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

echo "7. Running Diagnostic Check..."
"${INSTALL_DIR}/airguard-ctl" doctor

echo "=========================================================="
echo "    AirGuard AI macOS Beta Installation Complete!         "
echo "=========================================================="
echo "• Desktop App: ${APP_DIR}"
echo "• Control CLI: ${BIN_DIR}/airguard-ctl {status|start|stop|restart|logs|doctor}"
echo "• Service Daemon: ${PLIST_FILE}"
echo "• Database File: ${DATA_DIR}/airguard.db"
echo "• Logs: ${LOG_DIR}/gateway.log"
echo ""
echo "To start the background daemon: airguard-ctl start"
