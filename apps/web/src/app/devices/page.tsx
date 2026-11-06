"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Wind,
  Activity,
  Cpu,
  Plus,
  ShieldCheck,
  Power,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Sliders,
  RefreshCw,
  ExternalLink,
  Radio,
  Search,
  Wifi,
  Layers,
  HelpCircle,
  ArrowRight,
  Server,
  Zap,
  Info
} from "lucide-react";
import { api } from "@/lib/api";

type TabType = "my_devices" | "nearby" | "room_connections" | "library" | "troubleshooting";

export default function DevicesPage() {
  const [activeTab, setActiveTab] = useState<TabType>("my_devices");
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Gateway & Discovery
  const [gatewayStatus, setGatewayStatus] = useState<any | null>(null);
  const [discoveredServices, setDiscoveredServices] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);

  // Room Pairings Summary
  const [roomPairings, setRoomPairings] = useState<any[]>([]);

  // Catalog
  const [catalogItems, setCatalogItems] = useState<any[]>([]);
  const [catalogSearch, setCatalogSearch] = useState("");

  // Action status message
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const homeId = h[0].id;
        const [devs, rms, pairings, gw, cat] = await Promise.all([
          api.getDevices(homeId),
          api.getRooms(homeId),
          api.getAllPairingsSummary(homeId),
          api.getGatewayStatus(),
          api.getCatalogDevices()
        ]);
        setDevices(devs);
        setRooms(rms);
        setRoomPairings(pairings);
        setGatewayStatus(gw);
        setCatalogItems(cat);
      }
    } catch (e) {
      console.error("Error loading devices data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScanGateway = async () => {
    setScanning(true);
    try {
      const res = await api.scanGateway(2.5);
      setDiscoveredServices(res);
      setActionMessage(`Gateway scan complete: ${res.length} network service(s) detected.`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (e) {
      console.error(e);
    } finally {
      setScanning(false);
    }
  };

  const handleToggleAuth = async (devId: string, currentVal: boolean) => {
    await api.toggleDeviceAuth(devId, !currentVal);
    await loadData();
  };

  const handleToggleOverride = async (devId: string, currentVal: boolean) => {
    await api.toggleManualOverride(devId, !currentVal);
    await loadData();
  };

  const handleSendSpeed = async (devId: string, speed: number) => {
    try {
      const res = await api.sendDeviceCommand(devId, "set_speed", { speed });
      setActionMessage(res.message);
      setTimeout(() => setActionMessage(null), 4000);
      await loadData();
    } catch (e: any) {
      setActionMessage(e.message || "Command rejected by safety engine.");
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  const handleDeleteDevice = async (devId: string) => {
    if (!confirm("Are you sure you want to disconnect and delete this device?")) return;
    await api.deleteDevice(devId);
    await loadData();
  };

  const handleApplyPresetForRoom = async (roomSummary: any) => {
    if (!homes.length || !roomSummary.purifiers.length) return;
    const homeId = homes[0].id;
    const purifier = roomSummary.purifiers[0];
    const sensor = roomSummary.sensors[0];

    try {
      await api.applyAutomationPreset({
        home_id: homeId,
        room_id: roomSummary.room_id,
        preset_id: "clean_air_guard",
        purifier_device_id: purifier.id,
        sensor_device_id: sensor?.id,
        mode: "auto_control"
      });
      setActionMessage(`Automatic Clean Air Guard enabled for ${roomSummary.room_name}!`);
      setTimeout(() => setActionMessage(null), 4000);
      await loadData();
    } catch (e: any) {
      alert(e.message || "Failed to configure room pairing.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Devices & Integrations</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage your air purifiers, air-quality monitors, electronic noses, and local discovery gateway.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/devices/add"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" /> Connect New Device
          </Link>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionMessage && (
        <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 text-xs font-semibold text-primary flex items-center gap-2 animate-in fade-in">
          <Info className="w-4 h-4 shrink-0" />
          {actionMessage}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border overflow-x-auto pb-1 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("my_devices")}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "my_devices"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Layers className="w-3.5 h-3.5" /> My Devices ({devices.length})
        </button>

        <button
          onClick={() => setActiveTab("nearby")}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "nearby"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Radio className="w-3.5 h-3.5" /> Nearby Devices ({discoveredServices.length || "Scan"})
        </button>

        <button
          onClick={() => setActiveTab("room_connections")}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "room_connections"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Zap className="w-3.5 h-3.5" /> Room Connections
        </button>

        <button
          onClick={() => setActiveTab("library")}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "library"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Search className="w-3.5 h-3.5" /> Device Library
        </button>

        <button
          onClick={() => setActiveTab("troubleshooting")}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "troubleshooting"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <HelpCircle className="w-3.5 h-3.5" /> Troubleshooting
        </button>
      </div>

      {/* TAB 1: MY CONNECTED DEVICES */}
      {activeTab === "my_devices" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.length === 0 ? (
            <div className="col-span-3 p-12 text-center rounded-2xl bg-card border border-border text-sm text-muted-foreground space-y-3">
              <Layers className="w-8 h-8 text-muted-foreground mx-auto" />
              <div className="font-semibold text-foreground">No devices paired yet.</div>
              <p className="text-xs max-w-sm mx-auto">
                Connect your air purifier, AirGradient monitor, or AirGuard sensor to enable intelligent air quality automation.
              </p>
              <Link
                href="/devices/add"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold"
              >
                <Plus className="w-3.5 h-3.5" /> Connect Device
              </Link>
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
                  {/* Header & Badges */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-bold text-base block">{dev.name}</span>
                      <span className="text-xs text-muted-foreground block mt-0.5">
                        {dev.manufacturer || "Generic"} • {dev.model || "Standard"}
                      </span>
                    </div>

                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                          dev.connection_protocol === "simulation"
                            ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                            : "bg-primary/10 text-primary border border-primary/20"
                        }`}
                      >
                        {dev.connection_protocol}
                      </span>
                      {dev.is_controllable ? (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500">
                          Control Device
                        </span>
                      ) : (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500">
                          Sensor Station
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Capabilities List */}
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {dev.capabilities?.measurements?.slice(0, 4).map((m: any, idx: number) => (
                      <span
                        key={idx}
                        className="text-[10px] font-medium px-2 py-0.5 rounded bg-muted text-muted-foreground"
                      >
                        {typeof m === "string" ? m : m.type}
                      </span>
                    ))}
                    {dev.is_controllable && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-500">
                        Fan Speed 1-3
                      </span>
                    )}
                  </div>

                  {/* Purifier Controls */}
                  {dev.is_controllable && (
                    <div className="mt-5 p-3.5 rounded-xl bg-muted/40 border border-border space-y-3">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-muted-foreground">Manual Fan Speed</span>
                        <span className="text-foreground">
                          {dev.manual_override ? "Manual Override Active" : "Auto Mode"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {[1, 2, 3].map((speed) => (
                          <button
                            key={speed}
                            onClick={() => handleSendSpeed(dev.id, speed)}
                            className="flex-1 py-1.5 rounded-lg bg-card border border-border text-xs font-bold hover:bg-primary hover:text-primary-foreground transition-colors"
                          >
                            Speed {speed}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Automation & Override Toggles */}
                  {dev.is_controllable && (
                    <div className="mt-4 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-primary" /> Auto-Control Authorized
                        </span>
                        <input
                          type="checkbox"
                          checked={dev.automation_authorized}
                          onChange={() => handleToggleAuth(dev.id, dev.automation_authorized)}
                          className="toggle-checkbox h-4 w-4 rounded accent-primary cursor-pointer"
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground flex items-center gap-1.5">
                          <Sliders className="w-3.5 h-3.5 text-amber-500" /> Hold Manual Override
                        </span>
                        <input
                          type="checkbox"
                          checked={dev.manual_override}
                          onChange={() => handleToggleOverride(dev.id, dev.manual_override)}
                          className="toggle-checkbox h-4 w-4 rounded accent-amber-500 cursor-pointer"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Status & Delete */}
                <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        dev.is_online ? "bg-emerald-500 animate-pulse" : "bg-destructive"
                      }`}
                    />
                    <span className="text-muted-foreground font-medium">
                      {dev.is_online ? "Online & Calibrated" : "Offline"}
                    </span>
                  </div>

                  <button
                    onClick={() => handleDeleteDevice(dev.id)}
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                    title="Disconnect Device"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 2: NEARBY DEVICES & LOCAL GATEWAY */}
      {activeTab === "nearby" && (
        <div className="space-y-6">
          {/* Gateway Status Banner */}
          <div className="p-5 rounded-2xl bg-card border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold">Local Discovery Gateway</h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                    Online ({gatewayStatus?.platform || "Local"})
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 font-mono">
                  Host IP: {gatewayStatus?.local_ip || "127.0.0.1"} • mDNS Active:{" "}
                  {gatewayStatus?.mdns_active ? "Yes" : "Hybrid Mode"}
                </p>
              </div>
            </div>

            <button
              onClick={handleScanGateway}
              disabled={scanning}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {scanning ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Scanning Subnet...
                </>
              ) : (
                <>
                  <Radio className="w-3.5 h-3.5" /> Scan Local Network
                </>
              )}
            </button>
          </div>

          {/* Discovered Devices Table */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold">Detected Network Devices ({discoveredServices.length})</h3>
              <span className="text-xs text-amber-500 font-medium flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Strictly Unverified until Paired
              </span>
            </div>

            {discoveredServices.length === 0 ? (
              <div className="p-8 text-center rounded-2xl bg-card border border-border text-xs text-muted-foreground space-y-2">
                <div>No devices detected yet. Click "Scan Local Network" above.</div>
                <p className="text-[11px] max-w-md mx-auto">
                  The local discovery gateway listens for mDNS Zeroconf broadcasts from Home Assistant, ESPHome, AirGradient, and VeSync devices.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {discoveredServices.map((srv) => (
                  <div key={srv.id} className="p-5 rounded-2xl bg-card border border-border space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                          {srv.manufacturer}
                        </span>
                        <h4 className="text-sm font-bold text-foreground mt-0.5">{srv.name}</h4>
                        <span className="font-mono text-[11px] text-muted-foreground block mt-0.5">
                          {srv.ip}:{srv.port} • {srv.service_type}
                        </span>
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
                        Discovered (Unverified)
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-muted/40 text-[11px] text-muted-foreground space-y-1">
                      <div className="font-semibold text-foreground">Capabilities Preview:</div>
                      <div>
                        Measurements:{" "}
                        {srv.capabilities_preview?.measurements?.join(", ") || "None"}
                      </div>
                      <div>
                        Controls: {srv.capabilities_preview?.controls?.join(", ") || "None"}
                      </div>
                    </div>

                    <div className="pt-2 flex justify-end">
                      <Link
                        href="/devices/add"
                        className="flex items-center gap-1 px-3.5 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm"
                      >
                        Pair Device <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: ROOM CONNECTIONS & AUTOMATIC SENSOR-TO-PURIFIER PAIRING */}
      {activeTab === "room_connections" && (
        <div className="space-y-6">
          <div>
            <h3 className="text-base font-bold">Room Automation Pairings</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              AirGuard pairs air monitors to purifiers located in the same room, automatically adjusting filtration when particle or VOC levels rise.
            </p>
          </div>

          <div className="space-y-4">
            {roomPairings.map((rm) => (
              <div key={rm.room_id} className="p-6 rounded-2xl bg-card border border-border space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-foreground">{rm.room_name}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-muted text-muted-foreground uppercase">
                      {rm.room_type}
                    </span>
                  </div>

                  {rm.is_paired ? (
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center gap-1 border border-emerald-500/20">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Paired for Clean-Air Auto-Control
                    </span>
                  ) : (
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-500 flex items-center gap-1 border border-amber-500/20">
                      <AlertCircle className="w-3.5 h-3.5" /> Unpaired (Missing Sensor or Purifier)
                    </span>
                  )}
                </div>

                {/* Visual Mapping Arrow */}
                <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-center">
                  {/* Left: Sensor Station */}
                  <div className="md:col-span-3 p-4 rounded-xl bg-muted/40 border border-border">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                      Measurement Sensor
                    </span>
                    {rm.sensors.length > 0 ? (
                      <div className="mt-1">
                        <span className="text-xs font-bold text-foreground block">
                          {rm.sensors[0].name}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {rm.sensors[0].manufacturer} • {rm.sensors[0].model}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground italic block mt-1">
                        No sensor assigned to this room
                      </span>
                    )}
                  </div>

                  {/* Middle: Automation Logic Link */}
                  <div className="md:col-span-1 flex flex-col items-center justify-center text-center">
                    <ArrowRight className="w-5 h-5 text-primary hidden md:block" />
                    <span className="text-[9px] font-bold text-primary block mt-0.5">PM2.5 Control</span>
                  </div>

                  {/* Right: Purifier */}
                  <div className="md:col-span-3 p-4 rounded-xl bg-muted/40 border border-border">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                      Air Purifier / Fan
                    </span>
                    {rm.purifiers.length > 0 ? (
                      <div className="mt-1">
                        <span className="text-xs font-bold text-foreground block">
                          {rm.purifiers[0].name}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {rm.purifiers[0].manufacturer} • {rm.purifiers[0].model}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground italic block mt-1">
                        No purifier assigned to this room
                      </span>
                    )}
                  </div>
                </div>

                {/* Auto-Pair Action Button */}
                {rm.is_paired && (
                  <div className="pt-2 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      Active Automation: {rm.active_automation ? "Running (Hysteresis Guarded)" : "Disabled"}
                    </span>
                    <button
                      onClick={() => handleApplyPresetForRoom(rm)}
                      className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm"
                    >
                      {rm.active_automation ? "Update Auto Preset" : "Enable Clean Air Guard (1-Click)"}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: DEVICE LIBRARY & COMPATIBILITY SEARCH */}
      {activeTab === "library" && (
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold">Supported Device Directory</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Verified compatibility matrix for consumer air purifiers, laser monitors, and electronic noses.
              </p>
            </div>
            <div className="relative w-full md:w-72">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search brand or model..."
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-card border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {catalogItems
              .filter((item) => {
                if (!catalogSearch) return true;
                const q = catalogSearch.toLowerCase();
                return (
                  item.brand.toLowerCase().includes(q) ||
                  item.model_name.toLowerCase().includes(q) ||
                  item.summary.toLowerCase().includes(q)
                );
              })
              .map((item) => (
                <div key={item.id} className="p-5 rounded-2xl bg-card border border-border flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                          {item.brand}
                        </span>
                        <h4 className="text-xs font-bold text-foreground mt-0.5">{item.model_name}</h4>
                      </div>
                      {item.is_supported ? (
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                          Supported
                        </span>
                      ) : (
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">
                          Unsupported
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-muted-foreground mt-2 line-clamp-3">{item.summary}</p>

                    <div className="mt-3 pt-3 border-t border-border space-y-1 text-[11px] text-muted-foreground">
                      <div>
                        <strong className="text-foreground">Route:</strong> {item.recommended_route}
                      </div>
                      <div>
                        <strong className="text-foreground">Controls:</strong>{" "}
                        {item.supported_controls?.length > 0
                          ? item.supported_controls.join(", ")
                          : "None (Sensor only)"}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-border flex justify-end">
                    <Link
                      href="/devices/add"
                      className="text-xs font-bold text-primary hover:underline flex items-center gap-1"
                    >
                      Connect Model <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* TAB 5: DEVICE TROUBLESHOOTING & DIAGNOSTICS */}
      {activeTab === "troubleshooting" && (
        <div className="space-y-6">
          <div>
            <h3 className="text-base font-bold">Device Diagnostics & Health Check</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Verify your local network reachability, sensor baselines, and integration tokens.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Check 1: Gateway */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground flex items-center gap-2">
                  <Server className="w-4 h-4 text-emerald-500" /> Local Discovery Gateway
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                  HEALTHY
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                The gateway is listening on network interfaces: {gatewayStatus?.interfaces?.join(", ") || "en0"}. Local mDNS resolution active.
              </p>
            </div>

            {/* Check 2: Encryption */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" /> Credential Encryption at Rest
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                  ENCRYPTED
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Home Assistant access tokens and MQTT passwords are encrypted using AES-256-GCM. Plaintext is never exposed in client responses.
              </p>
            </div>

            {/* Check 3: Sensor Warmup Guard */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-500" /> BME688 MOX Conditioning
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500">
                  ACTIVE
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Physical sensor drift protection active. 15-minute thermal stabilization enforced after cold boots before ML odor classification.
              </p>
            </div>

            {/* Check 4: Stale Telemetry Protection */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-blue-500" /> Stale Telemetry Protection
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
                  5-MIN TIMEOUT
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Readings older than 300 seconds are flagged as STALE. The automation engine automatically suspends fan speed changes on stale readings.
              </p>
            </div>
          </div>

          {/* Understandable Remedies Guide */}
          <div className="p-6 rounded-2xl bg-card border border-border space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Frequently Encountered Remedies
            </h4>
            <div className="space-y-2.5 text-xs">
              <div className="p-3 rounded-xl bg-muted/40 space-y-1">
                <div className="font-bold text-foreground">Purifier not responding to automated fan commands?</div>
                <p className="text-muted-foreground">
                  Check if a family member pressed a physical button on the purifier. AirGuard enforces an inviolable 30-minute manual override hold. You can toggle off manual override on the device card.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-muted/40 space-y-1">
                <div className="font-bold text-foreground">Home Assistant connection times out?</div>
                <p className="text-muted-foreground">
                  Verify your Home Assistant URL. If using local IP without SSL certificates, use <code className="bg-card px-1 rounded font-mono">http://</code> rather than <code className="bg-card px-1 rounded font-mono">https://</code>.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-muted/40 space-y-1">
                <div className="font-bold text-foreground">AirGradient monitor not appearing in Nearby scan?</div>
                <p className="text-muted-foreground">
                  Ensure the AirGradient ONE is on the same 2.4GHz Wi-Fi subnet and that "Local Server Mode" is enabled in its onboard settings.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
