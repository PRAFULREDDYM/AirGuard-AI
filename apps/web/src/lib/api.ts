const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  let token = typeof window !== "undefined" ? localStorage.getItem("airguard_token") : null;

  // Auto-login demo if token missing
  if (!token && typeof window !== "undefined") {
    try {
      const demoRes = await fetch(`${API_BASE}/auth/demo-login`, { method: "POST" });
      if (demoRes.ok) {
        const data = await demoRes.json();
        token = data.access_token;
        localStorage.setItem("airguard_token", token as string);
        localStorage.setItem("airguard_user", JSON.stringify(data.user));
      }
    } catch (e) {
      console.warn("Could not auto-login demo:", e);
    }
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("airguard_token");
  }

  return response;
}

export const api = {
  // Auth
  async demoLogin() {
    const res = await fetch(`${API_BASE}/auth/demo-login`, { method: "POST" });
    const data = await res.json();
    if (res.ok && typeof window !== "undefined") {
      localStorage.setItem("airguard_token", data.access_token);
      localStorage.setItem("airguard_user", JSON.stringify(data.user));
    }
    return data;
  },

  async getMe() {
    const res = await fetchWithAuth("/auth/me");
    return res.json();
  },

  // Homes & Rooms
  async getHomes() {
    const res = await fetchWithAuth("/homes");
    return res.json();
  },

  async getRooms(homeId: string) {
    const res = await fetchWithAuth(`/rooms?home_id=${homeId}`);
    return res.json();
  },

  async getRoomDetails(roomId: string) {
    const res = await fetchWithAuth(`/rooms/${roomId}`);
    return res.json();
  },

  async createRoom(data: { home_id: string; name: string; room_type: string; floor: number }) {
    const res = await fetchWithAuth("/rooms", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  // Devices
  async getDevices(homeId: string) {
    const res = await fetchWithAuth(`/devices?home_id=${homeId}`);
    return res.json();
  },

  async createDevice(data: any) {
    const res = await fetchWithAuth("/devices", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async testConnection(provider: string, credentials: any) {
    const res = await fetchWithAuth("/devices/test-connection", {
      method: "POST",
      body: JSON.stringify({ provider, credentials })
    });
    return res.json();
  },

  async discoverDevices(provider: string, credentials: any) {
    const res = await fetchWithAuth("/devices/discover", {
      method: "POST",
      body: JSON.stringify({ provider, credentials })
    });
    return res.json();
  },

  async toggleDeviceAuth(deviceId: string, authorized: boolean) {
    const res = await fetchWithAuth(`/devices/${deviceId}/authorization?authorized=${authorized}`, {
      method: "PATCH"
    });
    return res.json();
  },

  async toggleManualOverride(deviceId: string, override: boolean) {
    const res = await fetchWithAuth(`/devices/${deviceId}/manual-override?override=${override}`, {
      method: "PATCH"
    });
    return res.json();
  },

  async sendDeviceCommand(deviceId: string, command: string, parameters: any = {}) {
    const res = await fetchWithAuth(`/devices/${deviceId}/command`, {
      method: "POST",
      body: JSON.stringify({ command, parameters })
    });
    return res.json();
  },

  async refreshDeviceHealth(deviceId: string) {
    const res = await fetchWithAuth(`/devices/${deviceId}/refresh-health`, {
      method: "POST"
    });
    return res.json();
  },

  async disconnectDevice(deviceId: string) {
    const res = await fetchWithAuth(`/devices/${deviceId}/disconnect`, {
      method: "POST"
    });
    return res.json();
  },

  // Readings
  async getReadings(params: { roomId?: string; deviceId?: string; hours?: number; measurement_type?: string }) {
    const q = new URLSearchParams();
    if (params.roomId) q.append("room_id", params.roomId);
    if (params.deviceId) q.append("device_id", params.deviceId);
    if (params.hours) q.append("hours", params.hours.toString());
    if (params.measurement_type) q.append("measurement_type", params.measurement_type);

    const res = await fetchWithAuth(`/readings?${q.toString()}`);
    return res.json();
  },

  async triggerSimulationTick(scenario: string = "normal") {
    const res = await fetchWithAuth(`/readings/simulation/tick?scenario=${scenario}`, {
      method: "POST"
    });
    return res.json();
  },

  // Events & Alerts
  async getEvents(params: { roomId?: string; severity?: string } = {}) {
    const q = new URLSearchParams();
    if (params.roomId) q.append("room_id", params.roomId);
    if (params.severity) q.append("severity", params.severity);

    const res = await fetchWithAuth(`/events?${q.toString()}`);
    return res.json();
  },

  async acknowledgeEvent(eventId: string, feedback?: string) {
    const res = await fetchWithAuth(`/events/${eventId}/acknowledge`, {
      method: "PATCH",
      body: JSON.stringify({ user_feedback: feedback })
    });
    return res.json();
  },

  async getAlerts(homeId: string) {
    const res = await fetchWithAuth(`/events/alerts?home_id=${homeId}`);
    return res.json();
  },

  // Automations
  async getAutomations(homeId: string) {
    const res = await fetchWithAuth(`/automations?home_id=${homeId}`);
    return res.json();
  },

  async createAutomation(data: any) {
    const res = await fetchWithAuth("/automations", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async updateAutomation(ruleId: string, data: any) {
    const res = await fetchWithAuth(`/automations/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getExecutions() {
    const res = await fetchWithAuth("/automations/executions");
    return res.json();
  },

  // AI & Models
  async predictMolecularOdor(smiles: string) {
    const res = await fetchWithAuth("/models/molecular/predict", {
      method: "POST",
      body: JSON.stringify({ smiles })
    });
    return res.json();
  },

  async getOdorDescriptors() {
    const res = await fetchWithAuth("/models/molecular/descriptors");
    return res.json();
  },

  async getMolecularBenchmark() {
    const res = await fetchWithAuth("/models/molecular/benchmark");
    return res.json();
  },

  async getEnoseBenchmark() {
    const res = await fetchWithAuth("/models/enose/benchmark");
    return res.json();
  },

  async getModelVersions() {
    const res = await fetchWithAuth("/models/versions");
    return res.json();
  },

  async getSessions() {
    const res = await fetchWithAuth("/models/sessions");
    return res.json();
  },

  async createSession(data: any) {
    const res = await fetchWithAuth("/models/sessions", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async trainSensorClassifier(name: string) {
    const res = await fetchWithAuth(`/models/train-classifier?model_name=${encodeURIComponent(name)}`, {
      method: "POST"
    });
    return res.json();
  },

  // Gateway & Discovery
  async getGatewayStatus() {
    const res = await fetchWithAuth("/gateway/status");
    return res.json();
  },

  async scanGateway(timeout: number = 2.0) {
    const res = await fetchWithAuth(`/gateway/scan?timeout=${timeout}`, {
      method: "POST"
    });
    return res.json();
  },

  async probeDevice(host: string, port?: number) {
    const res = await fetchWithAuth("/gateway/probe", {
      method: "POST",
      body: JSON.stringify({ host, port })
    });
    return res.json();
  },

  // Catalog & Compatibility
  async getCatalogDevices(params: { q?: string; category?: string; supported_only?: boolean } = {}) {
    const q = new URLSearchParams();
    if (params.q) q.append("q", params.q);
    if (params.category) q.append("category", params.category);
    if (params.supported_only !== undefined) q.append("supported_only", params.supported_only.toString());
    const res = await fetchWithAuth(`/catalog/devices?${q.toString()}`);
    return res.json();
  },

  async getCatalogDevice(id: string) {
    const res = await fetchWithAuth(`/catalog/devices/${id}`);
    return res.json();
  },

  // Room Pairings
  async getRoomPairings(roomId: string) {
    const res = await fetchWithAuth(`/rooms/${roomId}/pairings`);
    return res.json();
  },

  async getAllPairingsSummary(homeId: string) {
    const res = await fetchWithAuth(`/rooms/all/pairings-summary?home_id=${homeId}`);
    return res.json();
  },

  // Automation Presets
  async getAutomationPresets() {
    const res = await fetchWithAuth("/automations/presets");
    return res.json();
  },

  async applyAutomationPreset(data: {
    home_id: string;
    room_id: string;
    preset_id: string;
    purifier_device_id: string;
    sensor_device_id?: string;
    mode: "monitor_only" | "notify_only" | "auto_control";
  }) {
    const res = await fetchWithAuth("/automations/apply-preset", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async deleteDevice(deviceId: string) {
    const res = await fetchWithAuth(`/devices/${deviceId}`, {
      method: "DELETE"
    });
    return res.json();
  },

  async deleteAutomation(ruleId: string) {
    const res = await fetchWithAuth(`/automations/${ruleId}`, {
      method: "DELETE"
    });
    return res.json();
  },

  async pauseAllAutomations(homeId: string, paused: boolean = true) {
    const res = await fetchWithAuth(`/automations/pause-all?home_id=${homeId}&paused=${paused}`, {
      method: "POST"
    });
    return res.json();
  },

  // Consents & Permissions
  async getConsents(activeOnly: boolean = false) {
    const res = await fetchWithAuth(`/consents?active_only=${activeOnly}`);
    return res.json();
  },

  async grantConsent(data: {
    home_id?: string;
    device_id?: string;
    integration_scope?: string;
    permission_type: string;
    authorized_actions?: string[];
    consent_version?: string;
    consent_origin?: string;
  }) {
    const res = await fetchWithAuth("/consents", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async revokeConsent(consentId: string) {
    const res = await fetchWithAuth(`/consents/${consentId}/revoke`, {
      method: "PATCH"
    });
    return res.json();
  },

  async getConsentStatus() {
    const res = await fetchWithAuth("/consents/status");
    return res.json();
  },

  // Notifications & Alerts
  async getNotificationPreferences(homeId: string) {
    const res = await fetchWithAuth(`/notifications/preferences?home_id=${homeId}`);
    return res.json();
  },

  async setNotificationPreference(data: any) {
    const res = await fetchWithAuth("/notifications/preferences", {
      method: "POST",
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getNotificationHistory(homeId: string, unreadOnly: boolean = false) {
    const res = await fetchWithAuth(`/notifications/history?home_id=${homeId}&unread_only=${unreadOnly}`);
    return res.json();
  },

  async markAlertRead(alertId: string) {
    const res = await fetchWithAuth(`/notifications/${alertId}/read`, {
      method: "PATCH"
    });
    return res.json();
  },

  async markAllAlertsRead(homeId: string) {
    const res = await fetchWithAuth(`/notifications/mark-all-read?home_id=${homeId}`, {
      method: "POST"
    });
    return res.json();
  },

  async sendTestNotification(homeId: string, channel: string = "IN_APP") {
    const res = await fetchWithAuth("/notifications/test", {
      method: "POST",
      body: JSON.stringify({ home_id: homeId, channel })
    });
    return res.json();
  },

  // User Data Privacy & Retention
  async exportUserData() {
    const res = await fetchWithAuth("/auth/export-data");
    return res.json();
  },

  async deleteAccountData() {
    const res = await fetchWithAuth("/auth/delete-account-data", {
      method: "DELETE"
    });
    return res.json();
  }
};

