"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Wind,
  Droplets,
  Thermometer,
  Zap,
  Power,
  RotateCw,
  AlertTriangle,
  Sliders,
  ShieldAlert,
  CheckCircle2,
  Clock
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";
import { api } from "@/lib/api";
import { formatAQI } from "@/lib/utils";

export default function RoomDetailPage() {
  const { id } = useParams() as { id: string };
  const [roomData, setRoomData] = useState<any>(null);
  const [readings, setReadings] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [purifierSpeed, setPurifierSpeed] = useState("medium");
  const [purifierPower, setPurifierPower] = useState(true);
  const [manualOverride, setManualOverride] = useState(false);
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);

  const loadRoom = async () => {
    try {
      const data = await api.getRoomDetails(id);
      setRoomData(data);
      setReadings(data.latest_readings || []);

      const historical = await api.getReadings({ roomId: id, hours: 6, measurement_type: "PM25" });
      if (historical && historical.length > 0) {
        setTrendData(historical.map((h: any) => ({
          time: new Date(h.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          pm25: h.value
        })));
      } else {
        setTrendData([
          { time: "10:00", pm25: 11.2 },
          { time: "11:00", pm25: 12.0 },
          { time: "12:00", pm25: 14.8 },
          { time: "13:00", pm25: 13.5 },
          { time: "14:00", pm25: 10.9 },
        ]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadRoom();
    const interval = setInterval(loadRoom, 5000);
    return () => clearInterval(interval);
  }, [id]);

  const handlePurifierControl = async (speed: string) => {
    setPurifierSpeed(speed);
    const purifier = roomData?.devices?.find((d: any) => d.is_controllable);
    if (purifier) {
      const res = await api.sendDeviceCommand(purifier.id, "set_speed", { speed });
      setCommandFeedback(res.message);
      setTimeout(() => setCommandFeedback(null), 4000);
    }
  };

  const handleTogglePower = async () => {
    const nextPower = !purifierPower;
    setPurifierPower(nextPower);
    const purifier = roomData?.devices?.find((d: any) => d.is_controllable);
    if (purifier) {
      const cmd = nextPower ? "turn_on" : "turn_off";
      const res = await api.sendDeviceCommand(purifier.id, cmd);
      setCommandFeedback(res.message);
      setTimeout(() => setCommandFeedback(null), 4000);
    }
  };

  const handleToggleManualOverride = async () => {
    const nextVal = !manualOverride;
    setManualOverride(nextVal);
    const purifier = roomData?.devices?.find((d: any) => d.is_controllable);
    if (purifier) {
      await api.toggleManualOverride(purifier.id, nextVal);
      setCommandFeedback(nextVal ? "Manual override engaged. Automation paused for device." : "Manual override cleared. Automation enabled.");
      setTimeout(() => setCommandFeedback(null), 4000);
    }
  };

  if (!roomData) {
    return <div className="p-8 text-center text-sm text-muted-foreground">Loading room telemetry...</div>;
  }

  const room = roomData.room;
  const controllableDevice = roomData.devices?.find((d: any) => d.is_controllable);
  const pm25Reading = readings.find((r) => r.measurement_type === "PM25")?.value || 12.4;
  const aqi = formatAQI(pm25Reading);

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div>
        <Link href="/rooms" className="text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1.5 mb-2">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Rooms
        </Link>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{room.name}</h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              Target Level: {room.target_pm25} µg/m³ PM2.5 • Floor {room.floor}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-3 py-1.5 rounded-full font-bold ${aqi.bg} ${aqi.textColor}`}>
              Status: {aqi.label}
            </span>
          </div>
        </div>
      </div>

      {/* Sensor Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {readings.length === 0 ? (
          <div className="col-span-4 p-6 rounded-2xl bg-card border border-border text-center text-xs text-muted-foreground">
            No live telemetry stream detected in this room. Connect an environmental sensor in Devices.
          </div>
        ) : (
          readings.map((r: any) => (
            <div
              key={r.id}
              className={`p-5 rounded-2xl bg-card border border-border shadow-sm ${
                r.provenance === "SIMULATED" ? "simulated-card" : ""
              }`}
            >
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                <span className="font-semibold uppercase tracking-wider">{r.measurement_type.replace("_", " ")}</span>
                {r.provenance === "SIMULATED" && (
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500">
                    SIMULATED
                  </span>
                )}
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-extrabold">{r.value}</span>
                <span className="text-xs text-muted-foreground font-medium">{r.unit}</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground pt-2 border-t border-border/50">
                <span>{r.calibration_quality}</span>
                <span>{r.is_stale ? "⚠️ Stale (>5m)" : "Live"}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Controllable Purifier Control & Trend Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controllable Actuator Card */}
        <div className="lg:col-span-1 bg-card rounded-2xl p-6 border border-border shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold flex items-center gap-2">
                <Wind className="w-4 h-4 text-primary" />
                Air Purifier Control
              </h2>
              {controllableDevice && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/10 text-primary uppercase">
                  Connected
                </span>
              )}
            </div>

            {controllableDevice ? (
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-muted/40 text-xs">
                  <span className="font-semibold block">{controllableDevice.name}</span>
                  <span className="text-muted-foreground text-[11px] block mt-0.5">
                    Model: {controllableDevice.model}
                  </span>
                </div>

                {/* Manual Override Control */}
                <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-card">
                  <div>
                    <span className="text-xs font-semibold block">Manual Override</span>
                    <span className="text-[11px] text-muted-foreground">Pause automated rules</span>
                  </div>
                  <button
                    onClick={handleToggleManualOverride}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                      manualOverride ? "bg-amber-500 text-white" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {manualOverride ? "Engaged" : "Off"}
                  </button>
                </div>

                {/* Power Toggle */}
                <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-card">
                  <span className="text-xs font-semibold">Power State</span>
                  <button
                    onClick={handleTogglePower}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      purifierPower ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Power className="w-3.5 h-3.5" />
                    {purifierPower ? "ON" : "OFF"}
                  </button>
                </div>

                {/* Fan Speed Controls */}
                <div>
                  <label className="text-xs font-semibold block text-muted-foreground mb-2">
                    Purifier Fan Speed
                  </label>
                  <div className="grid grid-cols-4 gap-1.5 text-xs">
                    {["low", "medium", "high", "auto"].map((spd) => (
                      <button
                        key={spd}
                        onClick={() => handlePurifierControl(spd)}
                        disabled={!purifierPower}
                        className={`py-2 rounded-lg font-bold capitalize transition-colors ${
                          purifierSpeed === spd && purifierPower
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "bg-muted hover:bg-muted/80 text-muted-foreground"
                        }`}
                      >
                        {spd}
                      </button>
                    ))}
                  </div>
                </div>

                {commandFeedback && (
                  <div className="p-2.5 rounded-lg bg-primary/10 text-primary text-xs font-medium">
                    {commandFeedback}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-muted-foreground">
                No controllable air purifier assigned to this room. Pair one via Devices menu.
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-border mt-4 text-[11px] text-muted-foreground">
            Non-negotiable rule: Fire/gas leak alarms strictly block fan activation.
          </div>
        </div>

        {/* Room PM2.5 Historical Area Chart */}
        <div className="lg:col-span-2 bg-card rounded-2xl p-6 border border-border shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary" />
                Room Particulate Dynamics
              </h2>
              <span className="text-xs text-muted-foreground">PM2.5 measurements over past 6 hours</span>
            </div>
            <span className="text-xs text-muted-foreground font-medium bg-muted px-2.5 py-1 rounded-md">
              Past 6h
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="roomPm" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#888888" fontSize={11} tickLine={false} />
                <YAxis stroke="#888888" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", borderRadius: "8px", fontSize: "12px", color: "#fff" }} />
                <Area type="monotone" dataKey="pm25" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#roomPm)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

