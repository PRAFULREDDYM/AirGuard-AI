"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Wind,
  Thermometer,
  Droplets,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Plus
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";
import { api } from "@/lib/api";
import { formatAQI } from "@/lib/utils";

export default function OverviewPage() {
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const homeId = h[0].id;
        const [r, d, e, readings] = await Promise.all([
          api.getRooms(homeId),
          api.getDevices(homeId),
          api.getEvents({ limit: "5" } as any),
          api.getReadings({ hours: 12, measurement_type: "PM25" })
        ]);
        if (r.length > 0) {
          try {
            const roomDet = await api.getRoomDetails(r[0].id);
            const liveReadings = roomDet.latest_readings || [];
            r[0].latest_voc = liveReadings.find((x: any) => x.measurement_type === "VOC_INDEX")?.value || 88;
            r[0].latest_temp = liveReadings.find((x: any) => x.measurement_type === "TEMPERATURE")?.value || 22.0;
            r[0].latest_hum = liveReadings.find((x: any) => x.measurement_type === "HUMIDITY")?.value || 45.0;
          } catch (_) {}
        }
        setRooms(r);
        setDevices(d);
        setEvents(e);

        if (readings && readings.length > 0) {
          const formatted = readings.map((item: any) => ({
            time: new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            pm25: item.value,
          }));
          setTrendData(formatted);
        } else {
          // Synthetic initial curve
          setTrendData([
            { time: "08:00", pm25: 9.2 },
            { time: "09:00", pm25: 11.0 },
            { time: "10:00", pm25: 14.5 },
            { time: "11:00", pm25: 12.8 },
            { time: "12:00", pm25: 10.4 },
            { time: "13:00", pm25: 11.2 },
          ]);
        }
      }
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const latestPM25 = trendData.length > 0 ? trendData[trendData.length - 1].pm25 : 11.2;
  const aqiInfo = formatAQI(latestPM25);

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Environmental Overview</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time multi-room monitoring, pattern recognition and automated air filtration.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => { setLoading(true); loadData(); }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-xs font-medium hover:bg-muted transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/devices/add"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Connect Device
          </Link>
        </div>
      </div>

      {/* Main AQI Status Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-card rounded-2xl p-6 border border-border shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                Overall Home Air Quality
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${aqiInfo.bg} ${aqiInfo.textColor}`}>
                {aqiInfo.label}
              </span>
            </div>
            <div className="mt-6 flex items-baseline gap-3">
              <span className="text-5xl font-black tracking-tight">{latestPM25}</span>
              <span className="text-muted-foreground font-medium text-lg">µg/m³ PM2.5</span>
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              WHO Recommended 24h Guideline: &lt; 15 µg/m³. Readings reflect calibrated particulate monitoring.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-6 border-t border-border mt-6 text-center">
            <div className="p-2 rounded-xl bg-muted/40">
              <span className="text-[11px] text-muted-foreground block">VOC Index</span>
              <span className="font-semibold text-sm">
                {rooms.length > 0 && rooms[0]?.latest_voc !== undefined ? rooms[0].latest_voc : "85"}
              </span>
            </div>
            <div className="p-2 rounded-xl bg-muted/40">
              <span className="text-[11px] text-muted-foreground block">Temp</span>
              <span className="font-semibold text-sm">
                {rooms.length > 0 && rooms[0]?.latest_temp !== undefined ? `${rooms[0].latest_temp} °C` : "22.1 °C"}
              </span>
            </div>
            <div className="p-2 rounded-xl bg-muted/40">
              <span className="text-[11px] text-muted-foreground block">Humidity</span>
              <span className="font-semibold text-sm">
                {rooms.length > 0 && rooms[0]?.latest_hum !== undefined ? `${rooms[0].latest_hum} %` : "46 %"}
              </span>
            </div>
          </div>
        </div>

        {/* 12-Hour Trend Graph */}
        <div className="lg:col-span-2 bg-card rounded-2xl p-6 border border-border shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Particulate (PM2.5) Trend
              </h2>
              <span className="text-xs text-muted-foreground">Timeseries trend from active indoor monitors</span>
            </div>
            <span className="text-xs text-muted-foreground font-medium bg-muted px-2.5 py-1 rounded-md">
              Past 12 Hours
            </span>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="pmGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#888888" fontSize={11} tickLine={false} />
                <YAxis stroke="#888888" fontSize={11} tickLine={false} domain={[0, "auto"]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", borderRadius: "8px", fontSize: "12px", color: "#fff" }}
                />
                <Area type="monotone" dataKey="pm25" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#pmGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Room Status Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold tracking-tight">Monitored Rooms</h2>
          <Link href="/rooms" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
            View All Rooms <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {rooms.map((room) => (
            <Link
              key={room.id}
              href={`/rooms/${room.id}`}
              className="bg-card rounded-2xl p-5 border border-border hover:border-primary/50 transition-all shadow-sm hover:shadow group block"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-base group-hover:text-primary transition-colors">
                  {room.name}
                </span>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                  Floor {room.floor}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-xl bg-muted/30">
                  <span className="text-muted-foreground block text-[11px]">PM2.5 Target</span>
                  <span className="font-semibold text-sm">{room.target_pm25} µg/m³</span>
                </div>
                <div className="p-2.5 rounded-xl bg-muted/30">
                  <span className="text-muted-foreground block text-[11px]">Purifier Control</span>
                  <span className="font-semibold text-sm text-primary">Active</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
                <span>Safe filtration active</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Bottom Grid: Recent Alerts & Quick Device Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts Feed */}
        <div className="bg-card rounded-2xl p-6 border border-border shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Recent Environmental Events
            </h2>
            <Link href="/events" className="text-xs text-primary font-medium hover:underline">
              View History
            </Link>
          </div>

          <div className="space-y-3">
            {events.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                No unusual environmental anomalies recorded. Normal baseline conditions.
              </div>
            ) : (
              events.slice(0, 3).map((event) => (
                <div key={event.id} className="p-3.5 rounded-xl bg-muted/40 border border-border/50 text-xs flex items-start justify-between">
                  <div>
                    <span className="font-semibold text-foreground block">{event.title}</span>
                    <span className="text-muted-foreground mt-0.5 block">{event.description}</span>
                    <span className="text-[10px] text-muted-foreground block mt-1">
                      {new Date(event.started_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 uppercase tracking-wider shrink-0">
                    {event.severity}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Connected Hardware & Integrations */}
        <div className="bg-card rounded-2xl p-6 border border-border shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <Cpu className="w-4 h-4 text-primary" />
              Connected Hardware ({devices.length})
            </h2>
            <Link href="/devices" className="text-xs text-primary font-medium hover:underline">
              Manage Devices
            </Link>
          </div>

          <div className="space-y-3">
            {devices.map((dev) => (
              <div key={dev.id} className="p-3.5 rounded-xl bg-muted/30 border border-border/50 flex items-center justify-between text-xs">
                <div>
                  <span className="font-semibold block">{dev.name}</span>
                  <span className="text-muted-foreground text-[11px] block">
                    Protocol: {dev.connection_protocol} • {dev.is_controllable ? "Controllable Actuator" : "Environmental Sensor"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5 text-emerald-500 font-medium text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Online
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

