"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Cpu,
  Plus,
  ShieldCheck,
  Power,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Sliders,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { api } from "@/lib/api";

export default function DevicesPage() {
  const [homes, setHomes] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDevices = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const d = await api.getDevices(h[0].id);
        setDevices(d);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const handleToggleAuth = async (devId: string, currentVal: boolean) => {
    await api.toggleDeviceAuth(devId, !currentVal);
    loadDevices();
  };

  const handleToggleOverride = async (devId: string, currentVal: boolean) => {
    await api.toggleManualOverride(devId, !currentVal);
    loadDevices();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Connected Devices</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage environmental sensors, air purifiers, and IoT protocol integrations.
          </p>
        </div>
        <Link
          href="/devices/add"
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Connect New Device
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.length === 0 ? (
          <div className="col-span-3 p-12 text-center rounded-2xl bg-card border border-border text-sm text-muted-foreground">
            No devices paired yet. Click "Connect New Device" to pair Home Assistant, AirGradient, or MQTT sensors.
          </div>
        ) : (
          devices.map((dev) => (
            <div
              key={dev.id}
              className={`p-6 rounded-2xl bg-card border border-border shadow-sm flex flex-col justify-between ${
                dev.connection_protocol === "simulation" ? "simulated-card" : ""
              }`}
            >
              <div>
                {/* Header & Protocol Pill */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-bold text-base block">{dev.name}</span>
                    <span className="text-xs text-muted-foreground block mt-0.5">
                      {dev.manufacturer || "Generic"} • {dev.model || "Sensor Station"}
                    </span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider bg-primary/10 text-primary shrink-0">
                    {dev.connection_protocol}
                  </span>
                </div>

                {/* Capabilities pills */}
                <div className="mt-4 flex flex-wrap gap-1.5">
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-muted text-muted-foreground">
                    {dev.is_controllable ? "Controllable Purifier" : "Environmental Sensor"}
                  </span>
                  {dev.firmware_version && (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-muted text-muted-foreground">
                      fw v{dev.firmware_version}
                    </span>
                  )}
                  {dev.connection_protocol === "simulation" && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-500">
                      SIMULATED
                    </span>
                  )}
                </div>

                {/* Control switches for actuators */}
                {dev.is_controllable && (
                  <div className="mt-5 space-y-2.5 pt-4 border-t border-border">
                    <div className="flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold block">Automation Permission</span>
                        <span className="text-[11px] text-muted-foreground">Allow automated fan rules</span>
                      </div>
                      <button
                        onClick={() => handleToggleAuth(dev.id, dev.automation_authorized)}
                        className={`px-3 py-1 rounded-lg font-bold text-xs transition-colors ${
                          dev.automation_authorized ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {dev.automation_authorized ? "Authorized" : "Blocked"}
                      </button>
                    </div>

                    <div className="flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold block">Manual Override</span>
                        <span className="text-[11px] text-muted-foreground">Suspend automations</span>
                      </div>
                      <button
                        onClick={() => handleToggleOverride(dev.id, dev.manual_override)}
                        className={`px-3 py-1 rounded-lg font-bold text-xs transition-colors ${
                          dev.manual_override ? "bg-amber-500 text-white" : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {dev.manual_override ? "Active" : "Normal"}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer status */}
              <div className="pt-4 border-t border-border mt-5 flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5 text-emerald-500 font-medium text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Online
                </span>
                <span className="text-[10px]">
                  Seen: {new Date(dev.last_seen_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

