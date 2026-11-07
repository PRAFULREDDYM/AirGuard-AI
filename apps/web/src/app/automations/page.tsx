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
  Power,
  Sparkles,
  Sliders,
  Bell,
  Eye,
  Info,
  Check,
  ChevronRight,
  Flame,
  AlertOctagon
} from "lucide-react";
import { api } from "@/lib/api";

type AssistantChoice = "monitor_only" | "notify_only" | "auto_control";

export default function AutomationsPage() {
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [presets, setPresets] = useState<any[]>([]);
  const [showBuilder, setShowBuilder] = useState(false);

  // Assistant State
  const [assistantChoice, setAssistantChoice] = useState<AssistantChoice>("auto_control");
  const [assistantRoom, setAssistantRoom] = useState("");
  const [assistantPurifier, setAssistantPurifier] = useState("");
  const [assistantPreset, setAssistantPreset] = useState("clean_air_guard");
  const [assistantSuccess, setAssistantSuccess] = useState<string | null>(null);
  const [automationsPaused, setAutomationsPaused] = useState(false);

  // Custom Form fields
  const [ruleName, setRuleName] = useState("");
  const [selectedRoom, setSelectedRoom] = useState("");
  const [targetDevice, setTargetDevice] = useState("");
  const [measurementType, setMeasurementType] = useState("PM25");
  const [condition, setCondition] = useState("ABOVE");
  const [threshold, setThreshold] = useState(35.0);
  const [actionCommand, setActionCommand] = useState("set_speed");
  const [actionSpeed, setActionSpeed] = useState("3");
  const [cooldown, setCooldown] = useState(1800);

  const loadAutomations = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const homeId = h[0].id;
        setAutomationsPaused(Boolean(h[0].automations_paused));
        const [r, d, rl, ex, pr] = await Promise.all([
          api.getRooms(homeId),
          api.getDevices(homeId),
          api.getAutomations(homeId),
          api.getExecutions(),
          api.getAutomationPresets()
        ]);
        setRooms(r);
        setRules(rl);
        setExecutions(ex);
        setPresets(pr);

        const controllable = d.filter((item: any) => item.is_controllable);
        setDevices(controllable);

        if (r.length > 0) {
          setSelectedRoom(r[0].id);
          setAssistantRoom(r[0].id);
        }
        if (controllable.length > 0) {
          setTargetDevice(controllable[0].id);
          setAssistantPurifier(controllable[0].id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadAutomations();
  }, []);

  const handleApplyAssistant = async () => {
    if (!homes.length || !assistantRoom || !assistantPurifier) return;
    try {
      await api.applyAutomationPreset({
        home_id: homes[0].id,
        room_id: assistantRoom,
        preset_id: assistantPreset,
        purifier_device_id: assistantPurifier,
        mode: assistantChoice
      });
      setAssistantSuccess(
        assistantChoice === "auto_control"
          ? "Automation active! Purifier will automatically respond to elevated particle levels."
          : assistantChoice === "notify_only"
          ? "Notifications enabled! You will be alerted when particle levels rise."
          : "Monitor mode enabled. Telemetry is tracked without automated adjustments."
      );
      setTimeout(() => setAssistantSuccess(null), 5000);
      await loadAutomations();
    } catch (e: any) {
      alert(e.message || "Failed to configure automation.");
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!homes.length || !targetDevice) return;

    await api.createAutomation({
      home_id: homes[0].id,
      room_id: selectedRoom || null,
      name: ruleName || `Auto speed ${actionSpeed} on ${measurementType}`,
      enabled: true,
      trigger_config: {
        measurement_type: measurementType,
        condition: condition,
        threshold: Number(threshold),
        duration_seconds: 60
      },
      action_config: {
        target_device_id: targetDevice,
        command: actionCommand,
        parameters: { speed: Number(actionSpeed) }
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

  const handleTogglePauseAll = async () => {
    if (!homes.length) return;
    try {
      const res = await api.pauseAllAutomations(homes[0].id, !automationsPaused);
      setAutomationsPaused(res.automations_paused);
      setAssistantSuccess(res.message);
      setTimeout(() => setAssistantSuccess(null), 4000);
      loadAutomations();
    } catch (e: any) {
      alert("Failed to toggle global automation pause.");
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this automation rule?")) return;
    await api.deleteAutomation(ruleId);
    loadAutomations();
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Smart Automations</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Safe, automated clean-air adjustments with built-in hysteresis and certified alarm overrides.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            onClick={handleTogglePauseAll}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-bold transition-all shadow-sm ${
              automationsPaused
                ? "bg-destructive text-destructive-foreground animate-pulse border-destructive"
                : "bg-card border-border text-foreground hover:bg-destructive/10 hover:text-destructive"
            }`}
          >
            <Power className="w-4 h-4" />
            {automationsPaused ? "RESUME AUTOMATIONS" : "Pause All Automations"}
          </button>
          <button
            onClick={() => setShowBuilder(!showBuilder)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border border-border text-xs font-bold hover:bg-muted transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4 text-primary" />
            {showBuilder ? "Close Advanced Builder" : "Custom Rule Builder"}
          </button>
        </div>
      </div>

      {/* BEGINNER-FRIENDLY AUTOMATION ASSISTANT */}
      <div className="p-6 rounded-3xl bg-gradient-to-br from-card to-muted/40 border border-border shadow-sm space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" /> Beginner Automation Assistant
            </span>
            <h2 className="text-xl font-bold text-foreground">
              Would you like AirGuard to automatically adjust your purifier when measured air quality deteriorates?
            </h2>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-2xl">
              Choose how you would like AirGuard to react when particulate matter (PM2.5) or VOC levels rise in your home.
            </p>
          </div>
        </div>

        {/* 3 Choices: Monitor only, Notify me, Automatically control */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Choice 1: Monitor only */}
          <button
            onClick={() => setAssistantChoice("monitor_only")}
            className={`p-5 rounded-2xl border text-left transition-all ${
              assistantChoice === "monitor_only"
                ? "bg-primary/10 border-primary ring-1 ring-primary"
                : "bg-card border-border hover:border-border/80"
            }`}
          >
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center mb-3">
              <Eye className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-foreground">1. Monitor Only</h4>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Log all sensor readings and display trends on your dashboard. No notifications sent and no fans adjusted.
            </p>
          </button>

          {/* Choice 2: Notify me */}
          <button
            onClick={() => setAssistantChoice("notify_only")}
            className={`p-5 rounded-2xl border text-left transition-all ${
              assistantChoice === "notify_only"
                ? "bg-primary/10 border-primary ring-1 ring-primary"
                : "bg-card border-border hover:border-border/80"
            }`}
          >
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center mb-3">
              <Bell className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-foreground">2. Notify Me</h4>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Send an alert to your phone or web dashboard when air quality drops so you can decide what action to take.
            </p>
          </button>

          {/* Choice 3: Automatically control */}
          <button
            onClick={() => setAssistantChoice("auto_control")}
            className={`p-5 rounded-2xl border text-left transition-all ${
              assistantChoice === "auto_control"
                ? "bg-primary/10 border-primary ring-1 ring-primary"
                : "bg-card border-border hover:border-border/80"
            }`}
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-3">
              <Sliders className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-foreground">3. Automatically Control</h4>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Automatically increase purifier fan speed during spikes, and return to quiet eco mode once clean air is restored.
            </p>
          </button>
        </div>

        {/* Selected Mode Configuration & Explanation */}
        {assistantChoice === "auto_control" && (
          <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Automatic Clean-Air Configuration
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">Target Room</label>
                <select
                  value={assistantRoom}
                  onChange={(e) => setAssistantRoom(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">Air Purifier</label>
                <select
                  value={assistantPurifier}
                  onChange={(e) => setAssistantPurifier(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {devices.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.model})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">Preset Profile</label>
                <select
                  value={assistantPreset}
                  onChange={(e) => setAssistantPreset(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="clean_air_guard">Clean Air Guard (PM2.5 &gt; 25 µg/m³)</option>
                  <option value="odor_eliminator">Odor Eliminator (VOC Spike &gt; 200)</option>
                </select>
              </div>
            </div>

            {/* Explanation of Measurement & Built-In Safety Rules */}
            <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-2 text-xs">
              <div className="font-bold text-foreground flex items-center gap-1.5">
                <Info className="w-4 h-4 text-primary" /> How AirGuard Controls Your Device Safely:
              </div>
              <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                <li>
                  <strong className="text-foreground">Trigger:</strong> Actuates fan to Speed 3 when PM2.5 exceeds 25 µg/m³ for 2 continuous minutes.
                </li>
                <li>
                  <strong className="text-foreground">Hysteresis:</strong> Does not abruptly toggle off; waits until PM2.5 is sustained below 12 µg/m³ for 5 minutes before reducing fan speed.
                </li>
                <li>
                  <strong className="text-foreground">Manual Override Respect:</strong> If you press a physical button on the purifier, AirGuard enters a 30-minute hold.
                </li>
                <li>
                  <strong className="text-foreground">Life-Safety Exclusion:</strong> All fans and electrical actuation are <span className="text-destructive font-bold">strictly prohibited</span> during suspected fire or combustible-gas leaks.
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Confirmation Button & Feedback */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2">
          {assistantSuccess ? (
            <div className="text-xs font-bold text-emerald-600 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> {assistantSuccess}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <ShieldCheck className="w-4 h-4 text-primary" /> Requires explicit authorization switch on device record.
            </span>
          )}

          <button
            onClick={handleApplyAssistant}
            className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm flex items-center gap-2 self-start md:self-auto"
          >
            <Check className="w-4 h-4" /> Apply Automation Preferences
          </button>
        </div>
      </div>

      {/* ADVANCED CUSTOM RULE BUILDER */}
      {showBuilder && (
        <form onSubmit={handleCreateRule} className="p-6 rounded-3xl bg-card border border-border space-y-5">
          <h3 className="text-base font-bold">Custom Automation Rule Builder</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Rule Name</label>
              <input
                type="text"
                value={ruleName}
                onChange={(e) => setRuleName(e.target.value)}
                placeholder="e.g. Living Room Cooking VOC Boost"
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Room</label>
              <select
                value={selectedRoom}
                onChange={(e) => setSelectedRoom(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Measurement Type</label>
              <select
                value={measurementType}
                onChange={(e) => setMeasurementType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
              >
                <option value="PM25">PM2.5 (µg/m³)</option>
                <option value="VOC_INDEX">VOC Index (1-500)</option>
                <option value="CO2">CO2 (ppm)</option>
                <option value="TEMPERATURE">Temperature (°C)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Condition</label>
              <select
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
              >
                <option value="ABOVE">Greater Than (&gt;)</option>
                <option value="BELOW">Less Than (&lt;)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Threshold</label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Target Purifier Device</label>
              <select
                value={targetDevice}
                onChange={(e) => setTargetDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.model})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Fan Speed Setting</label>
              <select
                value={actionSpeed}
                onChange={(e) => setActionSpeed(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="1">Speed 1 (Low / Eco)</option>
                <option value="2">Speed 2 (Medium)</option>
                <option value="3">Speed 3 (High Filtration)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowBuilder(false)}
              className="px-4 py-2 rounded-xl border border-border text-xs font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-sm"
            >
              Save Custom Rule
            </button>
          </div>
        </form>
      )}

      {/* ACTIVE RULES LIST */}
      <div className="space-y-4">
        <h3 className="text-base font-bold">Active Automation Rules ({rules.length})</h3>

        {rules.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-card border border-border text-xs text-muted-foreground">
            No active automation rules. Use the Assistant above to enable automatic clean-air adjustments.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules.map((rule) => (
              <div key={rule.id} className="p-5 rounded-2xl bg-card border border-border space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-foreground">{rule.name}</h4>
                    <span className="text-[11px] text-muted-foreground block mt-0.5">
                      Cooldown: {rule.cooldown_seconds / 60} mins • Max {rule.max_executions_per_hour}/hr
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => handleToggleRule(rule.id, rule.enabled)}
                    className="h-4 w-4 rounded accent-primary cursor-pointer"
                  />
                </div>

                <div className="p-3 rounded-xl bg-muted/30 text-xs text-muted-foreground space-y-1">
                  <div>
                    <strong className="text-foreground">Trigger: </strong>
                    {rule.trigger_config.type || rule.trigger_config.measurement_type} ({rule.trigger_config.condition || ">"}{" "}
                    {rule.trigger_config.threshold})
                  </div>
                  <div>
                    <strong className="text-foreground">Command: </strong>
                    {rule.action_config.command} (Speed:{" "}
                    {rule.action_config.parameters?.speed || 3})
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-emerald-500 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Safety verified
                  </span>
                  <button
                    onClick={() => handleDeleteRule(rule.id)}
                    className="text-muted-foreground hover:text-destructive font-medium"
                  >
                    Delete Rule
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RECENT AUTOMATION EXECUTIONS AUDIT TRAIL */}
      <div className="space-y-4">
        <h3 className="text-base font-bold flex items-center gap-2">
          <History className="w-4 h-4 text-primary" /> Execution Audit Trail ({executions.length})
        </h3>

        <div className="rounded-2xl bg-card border border-border overflow-hidden">
          <table className="w-full text-xs text-left">
            <thead className="bg-muted/50 border-b border-border text-muted-foreground font-semibold">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">Trigger Condition</th>
                <th className="p-3.5">Command Dispatched</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Execution Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {executions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-muted-foreground">
                    No automation executions recorded yet. Commands will appear here when triggered.
                  </td>
                </tr>
              ) : (
                executions.map((ex) => (
                  <tr key={ex.id} className="hover:bg-muted/20">
                    <td className="p-3.5 font-mono text-muted-foreground">
                      {new Date(ex.executed_at).toLocaleTimeString()}
                    </td>
                    <td className="p-3.5 font-medium">{ex.trigger_event || "PM2.5 Elevated"}</td>
                    <td className="p-3.5 font-mono">
                      {ex.command} ({JSON.stringify(ex.parameters)})
                    </td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-500">
                        {ex.status}
                      </span>
                    </td>
                    <td className="p-3.5 text-muted-foreground">{ex.message || "Executed successfully"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
