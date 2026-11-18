#!/usr/bin/env bash
# AirGuard AI — macOS Clean Uninstaller

set -e

echo "=== AirGuard AI Uninstallation ==="

INSTALL_DIR="${HOME}/.local/share/airguard-ai"
DATA_DIR="${HOME}/.airguard"
PLIST_FILE="${HOME}/Library/LaunchAgents/ai.airguard.gateway.plist"
APP_DIR="${HOME}/Applications/AirGuard AI.app"
BIN_LINK="${HOME}/.local/bin/airguard-ctl"

# 1. Unload and remove launchd agent
if [ -f "${PLIST_FILE}" ]; then
    echo "Stopping and unloading LaunchAgent..."
    launchctl unload "${PLIST_FILE}" 2>/dev/null || true
    rm -f "${PLIST_FILE}"
fi

# 2. Kill running processes
pkill -f "services.api.main:app" 2>/dev/null || true

# 3. Remove application binaries
rm -rf "${INSTALL_DIR}"
rm -rf "${APP_DIR}"
rm -f "${BIN_LINK}"
echo "Application bundle removed."

# 4. Prompt for data removal
if [ "$1" = "--purge-data" ]; then
    echo "Purging all user databases and logs..."
    rm -rf "${DATA_DIR}"
    rm -rf "${HOME}/Library/Logs/AirGuard"
    echo "All data removed."
else
    echo "Note: User data preserved at ${DATA_DIR}."
    echo "To remove all data, run: ./uninstall_macos.sh --purge-data"
fi

echo "AirGuard AI has been uninstalled."

