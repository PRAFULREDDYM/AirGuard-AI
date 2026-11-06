"use client";

import React, { useState, useEffect } from "react";
import {
  Zap,
  Plus,
  Play,
  ShieldCheck,
  Clock,
  CheckCircle2,
  AlertTriangle,
  History,
  Power
} from "lucide-react";
import { api } from "@/lib/api";

export default function AutomationsPage() {
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [showBuilder, setShowBuilder] = useState(false);

  // Form fields
  const [ruleName, setRuleName] = useState("");
  const [selectedRoom, setSelectedRoom] = useState("");
  const [targetDevice, setTargetDevice] = useState("");
  const [measurementType, setMeasurementType] = useState("PM25");
  const [condition, setCondition] = useState("ABOVE");
  const [threshold, setThreshold] = useState(35.0);
  const [actionCommand, setActionCommand] = useState("set_speed");
  const [actionSpeed, setActionSpeed] = useState("high");
  const [cooldown, setCooldown] = useState(1800);

  const loadAutomations = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const [r, d, rl, ex] = await Promise.all([
          api.getRooms(h[0].id),
          api.getDevices(h[0].id),
          api.getAutomations(h[0].id),
          api.getExecutions()
        ]);
        setRooms(r);
        setDevices(d.filter((item: any) => item.is_controllable));
        setRules(rl);
        setExecutions(ex);
        if (r.length > 0) setSelectedRoom(r[0].id);
        const controllable = d.filter((item: any) => item.is_controllable);
        if (controllable.length > 0) setTargetDevice(controllable[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadAutomations();
  }, []);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!homes.length || !targetDevice) return;

    await api.createAutomation({
      home_id: homes[0].id,
      room_id: selectedRoom || null,
      name: ruleName || `Auto ${actionSpeed} on ${measurementType}`,
      enabled: true,
      trigger_config: {
        measurement_type: measurementType,
        condition: condition,
        threshold: Number(threshold),
        duration_seconds: 60
      },
      action_config: {
        device_id: targetDevice,
        command: actionCommand,
        parameters: { speed: actionSpeed }
      },
      cooldown_seconds: Number(cooldown),
      max_executions_per_hour: 4
    });

    setRuleName("");
    setShowBuilder(false);
    loadAutomations();
  };

  const handleToggleRule = async (ruleId: string, currentEnabled: boolean) => {
    await api.updateAutomation(ruleId, { enabled: !currentEnabled });
    loadAutomations();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Smart-Device Automations</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Configure if-then environmental rules with safety constraints, cooldowns, and audit logging.
          </p>
        </div>
        <button
          onClick={() => setShowBuilder(!showBuilder)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Create Automation Rule
        </button>
      </div>

      {/* Safety Engine Invariant Alert Banner */}
      <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold block text-sm">AirGuard Automation Safety Core Active</span>
          <span className="text-[11px] mt-0.5 block opacity-90">
            Rules strictly enforce: No fan actuation during suspected combustible gas leaks; No ozone generators; User manual overrides immediately pause rules; Max 1 command/30s rate limits.
          </span>
        </div>
      </div>

      {/* Rule Builder Form Modal */}
      {showBuilder && (
        <form onSubmit={handleCreateRule} className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4 max-w-xl">
          <h2 className="text-base font-bold">New Automation Rule</h2>
          <div>
            <label className="text-xs font-semibold block text-muted-foreground mb-1">Rule Name</label>
            <input
              type="text"
              value={ruleName}
              onChange={(e) => setRuleName(e.target.value)}
              placeholder="e.g. Boost Purifier on Cooking Smoke"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold block text-muted-foreground mb-1">Trigger Sensor</label>
              <select
                value={measurementType}
                onChange={(e) => setMeasurementType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="PM25">PM2.5 (Particulate)</option>
                <option value="VOC_INDEX">VOC Index</option>
                <option value="CO2">CO2 (Direct NDIR)</option>
                <option value="TEMPERATURE">Temperature</option>
              </select>
            </div>
            <div>
              <label className="font-semibold block text-muted-foreground mb-1">Threshold Value</label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold block text-muted-foreground mb-1">Target Air Purifier</label>
              <select
                value={targetDevice}
                onChange={(e) => setTargetDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-semibold block text-muted-foreground mb-1">Target Speed</label>
              <select
                value={actionSpeed}
                onChange={(e) => setActionSpeed(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="high">High Speed</option>
                <option value="medium">Medium Speed</option>
                <option value="low">Low Speed</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold block text-muted-foreground mb-1">Cooldown Duration (Seconds)</label>
            <input
              type="number"
              value={cooldown}
              onChange={(e) => setCooldown(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowBuilder(false)}
              className="px-3.5 py-2 rounded-lg border border-border text-xs font-medium hover:bg-muted"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
            >
              Save Rule
            </button>
          </div>
        </form>
      )}

      {/* Rules List */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold tracking-tight">Active Automation Rules ({rules.length})</h2>
        {rules.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-card border border-border text-xs text-muted-foreground">
            No automation rules configured. Click "Create Automation Rule" to add one.
          </div>
        ) : (
          rules.map((rule) => (
            <div
              key={rule.id}
              className="p-5 rounded-2xl bg-card border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-base">{rule.name}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    rule.enabled ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"
                  }`}>
                    {rule.enabled ? "Active" : "Disabled"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  IF {rule.trigger_config?.measurement_type} {rule.trigger_config?.condition} {rule.trigger_config?.threshold} THEN set purifier speed to {rule.action_config?.parameters?.speed || "active"}.
                </p>
                <div className="flex items-center gap-4 text-[11px] text-muted-foreground mt-2">
                  <span>Cooldown: {rule.cooldown_seconds}s</span>
                  <span>Max/hr: {rule.max_executions_per_hour}</span>
                  {rule.last_triggered_at && (
                    <span>Last triggered: {new Date(rule.last_triggered_at).toLocaleTimeString()}</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleToggleRule(rule.id, rule.enabled)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                    rule.enabled ? "bg-destructive/10 text-destructive hover:bg-destructive/20" : "bg-primary text-primary-foreground hover:bg-primary/90"
                  }`}
                >
                  {rule.enabled ? "Disable Rule" : "Enable Rule"}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Execution Audit Log */}
      <div className="bg-card rounded-2xl p-6 border border-border shadow-sm space-y-4">
        <h2 className="text-base font-bold flex items-center gap-2">
          <History className="w-4 h-4 text-primary" />
          Automation Execution Audit Trail
        </h2>
        {executions.length === 0 ? (
          <div className="p-6 text-center text-xs text-muted-foreground">
            No execution logs recorded yet.
          </div>
        ) : (
          <div className="space-y-2">
            {executions.slice(0, 5).map((ex) => (
              <div key={ex.id} className="p-3 rounded-xl bg-muted/30 border border-border/50 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold block">{ex.command} (device: {ex.device_id.slice(0, 8)}...)</span>
                  <span className="text-muted-foreground text-[11px] block">{ex.reason}</span>
                </div>
                <div className="text-right">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    ex.status === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                  }`}>
                    {ex.status}
                  </span>
                  <span className="text-[10px] text-muted-foreground block mt-1">
                    {new Date(ex.triggered_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

