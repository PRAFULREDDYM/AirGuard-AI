"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  ShieldCheck,
  Server,
  Radio,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { api } from "@/lib/api";

export default function AddDeviceWizardPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState("home_assistant");
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [selectedRoom, setSelectedRoom] = useState("");

  // Connection form fields
  const [haUrl, setHaUrl] = useState("http://homeassistant.local:8123");
  const [haToken, setHaToken] = useState("");
  const [agHost, setAgHost] = useState("192.168.1.150");
  const [mqttHost, setMqttHost] = useState("localhost");
  const [mqttPort, setMqttPort] = useState(1883);

  // Discovery & state
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [discoveredDevices, setDiscoveredDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<any>(null);

  useEffect(() => {
    async function init() {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const r = await api.getRooms(h[0].id);
        setRooms(r);
        if (r.length > 0) setSelectedRoom(r[0].id);
      }
    }
    init();
  }, []);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    let creds: any = {};
    if (provider === "home_assistant") {
      creds = { base_url: haUrl, token: haToken };
    } else if (provider === "airgradient") {
      creds = { host: agHost };
    } else if (provider === "mqtt") {
      creds = { broker_host: mqttHost, broker_port: mqttPort };
    }

    try {
      const res = await api.testConnection(provider, creds);
      setTestResult(res);
      if (res.success) {
        // Run discovery
        const disc = await api.discoverDevices(provider, creds);
        setDiscoveredDevices(disc.devices || []);
        if (disc.devices?.length > 0) {
          setSelectedDevice(disc.devices[0]);
        }
      }
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || "Failed to connect to integration." });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveDevice = async () => {
    if (!homes.length) return;
    const homeId = homes[0].id;

    const deviceData = {
      home_id: homeId,
      room_id: selectedRoom || null,
      name: selectedDevice ? selectedDevice.name : `${provider.toUpperCase()} Device`,
      manufacturer: selectedDevice?.manufacturer || "Generic",
      model: selectedDevice?.model || "Standard",
      firmware_version: selectedDevice?.firmware_version || "1.0",
      connection_protocol: provider,
      is_controllable: selectedDevice?.is_controllable || false,
      capabilities: {
        measurements: selectedDevice?.supported_measurements || [{"type": "PM25", "unit": "µg/m³"}],
        controls: selectedDevice?.supported_controls || []
      }
    };

    await api.createDevice(deviceData);
    router.push("/devices");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link href="/devices" className="text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1.5">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Devices
      </Link>

      <div>
        <h1 className="text-3xl font-bold tracking-tight">Connect New Device</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Follow the guided wizard to connect real air-quality monitors, purifiers, or test adapters.
        </p>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-between text-xs font-medium text-muted-foreground border-b border-border pb-3">
        <span className={step >= 1 ? "text-primary font-bold" : ""}>1. Select Protocol</span>
        <span>•</span>
        <span className={step >= 2 ? "text-primary font-bold" : ""}>2. Connection Credentials</span>
        <span>•</span>
        <span className={step >= 3 ? "text-primary font-bold" : ""}>3. Discovery & Assign</span>
      </div>

      {/* Step 1: Provider Selection */}
      {step === 1 && (
        <div className="space-y-4">
          <label className="text-sm font-bold block">Choose Integration Protocol</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { id: "home_assistant", name: "Home Assistant", desc: "Connect local instance via Long-Lived Access Token", icon: Server },
              { id: "airgradient", name: "AirGradient Local API", desc: "Connect AirGradient ONE monitor via local IP", icon: Cpu },
              { id: "mqtt", name: "MQTT Broker", desc: "Subscribe to local telemetry or ESPHome discovery", icon: Radio },
              { id: "simulation", name: "Simulation Adapter", desc: "Generate realistic labeled test streams without hardware", icon: Sparkles },
            ].map((p) => {
              const Icon = p.icon;
              return (
                <div
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                    provider === p.id
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-border bg-card hover:bg-muted/50"
                  }`}
                >
                  <Icon className="w-6 h-6 text-primary mb-3" />
                  <span className="font-bold text-sm block">{p.name}</span>
                  <span className="text-xs text-muted-foreground mt-1 block">{p.desc}</span>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
            >
              Continue to Credentials <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Credentials and Connection Testing */}
      {step === 2 && (
        <div className="space-y-5 p-6 rounded-2xl bg-card border border-border shadow-sm">
          <h2 className="text-base font-bold capitalize">Configure {provider.replace("_", " ")}</h2>

          {provider === "home_assistant" && (
            <div className="space-y-4 text-xs">
              <div>
                <label className="font-semibold block text-muted-foreground mb-1">Instance URL</label>
                <input
                  type="text"
                  value={haUrl}
                  onChange={(e) => setHaUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="font-semibold block text-muted-foreground mb-1">Long-Lived Access Token</label>
                <input
                  type="password"
                  value={haToken}
                  onChange={(e) => setHaToken(e.target.value)}
                  placeholder="Bearer eyJhbGciOi..."
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          {provider === "airgradient" && (
            <div className="space-y-4 text-xs">
              <div>
                <label className="font-semibold block text-muted-foreground mb-1">AirGradient Device IP / Hostname</label>
                <input
                  type="text"
                  value={agHost}
                  onChange={(e) => setAgHost(e.target.value)}
                  placeholder="e.g. 192.168.1.150 or airgradient_001.local"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          {provider === "mqtt" && (
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="col-span-2">
                <label className="font-semibold block text-muted-foreground mb-1">Broker Host</label>
                <input
                  type="text"
                  value={mqttHost}
                  onChange={(e) => setMqttHost(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="font-semibold block text-muted-foreground mb-1">Port</label>
                <input
                  type="number"
                  value={mqttPort}
                  onChange={(e) => setMqttPort(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          {provider === "simulation" && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-200">
              The simulation adapter provides synthetic multi-sensor streams and controllable purifiers. All readings are labeled SIMULATED.
            </div>
          )}

          {/* Test Connection Button */}
          <div className="pt-2 flex items-center justify-between">
            <button
              onClick={() => setStep(1)}
              className="px-3 py-2 rounded-lg border border-border text-xs font-medium hover:bg-muted"
            >
              Back
            </button>
            <button
              onClick={handleTestConnection}
              disabled={testing}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 disabled:opacity-50"
            >
              {testing ? "Testing Connection..." : "Test Connection & Discover"}
            </button>
          </div>

          {testResult && (
            <div
              className={`p-3.5 rounded-xl text-xs flex items-center gap-2 ${
                testResult.success
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                  : "bg-destructive/10 text-destructive border border-destructive/20"
              }`}
            >
              {testResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
              <span>{testResult.message}</span>
            </div>
          )}

          {testResult?.success && (
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setStep(3)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700"
              >
                Proceed to Device Selection ({discoveredDevices.length} found) <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Discovery & Room Assignment */}
      {step === 3 && (
        <div className="space-y-5 p-6 rounded-2xl bg-card border border-border shadow-sm">
          <h2 className="text-base font-bold">Select Discovered Device & Assign Room</h2>

          {discoveredDevices.length === 0 ? (
            <div className="p-6 text-center text-xs text-muted-foreground">
              No hardware devices discovered on this instance. Check connection parameters.
            </div>
          ) : (
            <div className="space-y-3">
              <label className="text-xs font-semibold block text-muted-foreground">Discovered Hardware Inventory</label>
              {discoveredDevices.map((d) => (
                <div
                  key={d.id}
                  onClick={() => setSelectedDevice(d)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedDevice?.id === d.id
                      ? "border-primary bg-primary/5"
                      : "border-border bg-card hover:bg-muted/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm">{d.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-muted font-medium">
                      {d.is_controllable ? "Actuator / Purifier" : "Monitor"}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground block mt-1">
                    {d.manufacturer} • {d.model}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Room Assignment */}
          <div>
            <label className="text-xs font-semibold block text-muted-foreground mb-1">Assign to Room</label>
            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>{r.name} (Floor {r.floor})</option>
              ))}
            </select>
          </div>

          <div className="pt-3 flex items-center justify-between border-t border-border">
            <button
              onClick={() => setStep(2)}
              className="px-3 py-2 rounded-lg border border-border text-xs font-medium hover:bg-muted"
            >
              Back
            </button>
            <button
              onClick={handleSaveDevice}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
            >
              Complete Pairing & Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

