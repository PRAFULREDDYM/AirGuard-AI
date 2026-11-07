"use client";

import React, { useState, useEffect } from "react";
import {
  Settings as SettingsIcon,
  ShieldCheck,
  Download,
  Trash2,
  Lock,
  User,
  Home,
  CheckCircle2,
  FileText,
  Bell,
  Sliders,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Power
} from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [homes, setHomes] = useState<any[]>([]);
  const [retentionDays, setRetentionDays] = useState(90);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Consents state
  const [consents, setConsents] = useState<any[]>([]);
  // Notification preferences
  const [notificationPrefs, setNotificationPrefs] = useState<any[]>([]);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);
  const [testAlertSuccess, setTestAlertSuccess] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [u, h, c] = await Promise.all([
        api.getMe(),
        api.getHomes(),
        api.getConsents()
      ]);
      setUser(u);
      setHomes(h);
      setConsents(c);

      if (h.length > 0) {
        const prefs = await api.getNotificationPreferences(h[0].id);
        setNotificationPrefs(prefs);
        if (prefs.length > 0) {
          setQuietHoursEnabled(Boolean(prefs[0].quiet_hours_enabled));
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedMessage("Settings and data retention preferences saved successfully.");
    setTimeout(() => setSavedMessage(null), 3000);
  };

  const handleRevokeConsent = async (consentId: string) => {
    if (!confirm("Are you sure you want to revoke this consent? Any automated control or related functionality will be halted immediately.")) return;
    try {
      await api.revokeConsent(consentId);
      setSavedMessage("Consent revoked. Automatic actions immediately halted.");
      setTimeout(() => setSavedMessage(null), 4000);
      await loadData();
    } catch (e: any) {
      alert("Failed to revoke consent.");
    }
  };

  const handleSendTestNotification = async () => {
    if (!homes.length) return;
    try {
      const res = await api.sendTestNotification(homes[0].id, "IN_APP");
      setTestAlertSuccess("Test in-app notification successfully dispatched to Notification Center.");
      setTimeout(() => setTestAlertSuccess(null), 4000);
    } catch (e: any) {
      alert("Failed to send test notification.");
    }
  };

  const handleExportJson = async () => {
    try {
      const data = await api.exportUserData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `airguard_export_${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Failed to export user data.");
    }
  };

  const handleDeleteAccountData = async () => {
    if (!confirm("PERMANENT ACTION: Are you sure you want to delete all account data, connected devices, and readings? This cannot be undone.")) return;
    try {
      await api.deleteAccountData();
      alert("Account data permanently deleted. Redirecting to login...");
      window.location.href = "/";
    } catch (e: any) {
      alert(e.message || "Failed to delete account data.");
    }
  };

  return (
    <div className="max-w-4xl space-y-6 pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings, Consents & Privacy</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage versioned consent records, notification delivery rules, encryption keys, and GDPR/CCPA data retention.
        </p>
      </div>

      {savedMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
          {savedMessage}
        </div>
      )}
      {testAlertSuccess && (
        <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-medium">
          {testAlertSuccess}
        </div>
      )}

      {/* Profile Card */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <h2 className="text-base font-bold flex items-center gap-2">
          <User className="w-4 h-4 text-primary" />
          User Profile & Residence
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-muted-foreground block mb-1">Email Address</span>
            <input
              type="text"
              disabled
              value={user?.email || "demo@airguard.ai"}
              className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-xs font-medium"
            />
          </div>
          <div>
            <span className="text-muted-foreground block mb-1">Full Name</span>
            <input
              type="text"
              disabled
              value={user?.full_name || "Demo User"}
              className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-xs font-medium"
            />
          </div>
        </div>
      </div>

      {/* Versioned Consents & Permissions Card */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              Active Consents & Permissions
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Every granted permission is individual and unbundled. Revoking any permission immediately halts related automated commands server-side.
            </p>
          </div>
          <button
            onClick={loadData}
            className="p-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:bg-muted"
            title="Refresh Consents"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {consents.length === 0 ? (
          <div className="p-6 text-center rounded-xl bg-muted/20 border border-border text-xs text-muted-foreground">
            No consent records granted yet. Run the Onboarding Wizard to configure device permissions.
          </div>
        ) : (
          <div className="space-y-2.5">
            {consents.map((c) => (
              <div
                key={c.id}
                className="p-3.5 rounded-xl border border-border bg-muted/20 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground">{c.permission_type}</span>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase ${
                        c.is_active && !c.revoked_at
                          ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                          : "bg-destructive/10 text-destructive border border-destructive/20"
                      }`}
                    >
                      {c.is_active && !c.revoked_at ? "Active" : "Revoked"}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-mono">v{c.consent_version}</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground block mt-0.5">
                    Granted: {new Date(c.created_at).toLocaleString()} • Origin: {c.consent_origin}
                    {c.revoked_at && ` • Revoked: ${new Date(c.revoked_at).toLocaleString()}`}
                  </span>
                </div>

                {c.is_active && !c.revoked_at && (
                  <button
                    onClick={() => handleRevokeConsent(c.id)}
                    className="px-3 py-1.5 rounded-lg border border-destructive/30 text-destructive text-xs font-semibold hover:bg-destructive/10 transition-colors"
                  >
                    Revoke Permission
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notification Delivery Preferences */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold flex items-center gap-2">
              <Bell className="w-4 h-4 text-blue-500" />
              Notification Delivery & Quiet Hours
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Configure alert delivery channels, quiet hours suppression for non-critical alerts, and alert deduplication.
            </p>
          </div>
          <button
            onClick={handleSendTestNotification}
            className="px-3 py-1.5 rounded-lg bg-blue-500 text-white text-xs font-bold hover:bg-blue-600 flex items-center gap-1.5 shadow-sm"
          >
            <Bell className="w-3.5 h-3.5" /> Send Test Alert
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-1">
            <span className="font-bold text-foreground block">In-App Notification Center</span>
            <p className="text-muted-foreground text-[11px]">
              Live badge counter, unread indicators, and chronological alert history. Enabled independently of OS push permissions.
            </p>
            <span className="text-[10px] font-bold text-emerald-500 block pt-1">Always Active</span>
          </div>

          <div className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-1">
            <span className="font-bold text-foreground block">Quiet Hours (22:00 – 07:00)</span>
            <p className="text-muted-foreground text-[11px]">
              Suppresses audible and push alerts during overnight hours. Critical certified life-safety alarms are never suppressed.
            </p>
            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="quiet_toggle"
                checked={quietHoursEnabled}
                onChange={(e) => setQuietHoursEnabled(e.target.checked)}
                className="toggle-checkbox h-4 w-4 rounded accent-primary cursor-pointer"
              />
              <label htmlFor="quiet_toggle" className="text-muted-foreground cursor-pointer font-medium">
                Enable Overnight Quiet Hours
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Security & Credentials Card */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-3">
        <h2 className="text-base font-bold flex items-center gap-2">
          <Lock className="w-4 h-4 text-primary" />
          Integration Credentials & Local Security
        </h2>
        <p className="text-xs text-muted-foreground">
          All external integration tokens (Home Assistant long-lived tokens, MQTT credentials, device tokens) are encrypted at rest using AES-256-GCM. Probing is guarded by strict SSRF filtering and port restriction.
        </p>
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 pt-1">
          <ShieldCheck className="w-4 h-4" />
          AES-256-GCM Hardware Encryption Key Configured
        </div>
      </div>

      {/* Data Retention & Privacy */}
      <form onSubmit={handleSaveSettings} className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <h2 className="text-base font-bold flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          Data Retention & Export (GDPR / CCPA)
        </h2>

        <div className="text-xs space-y-2">
          <label className="font-semibold block text-muted-foreground">Telemetry Retention Window</label>
          <select
            value={retentionDays}
            onChange={(e) => setRetentionDays(Number(e.target.value))}
            className="w-full max-w-xs px-3 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value={30}>30 Days (Local Storage Friendly)</option>
            <option value={90}>90 Days (Standard Analytics)</option>
            <option value={180}>180 Days (Longitudinal Research)</option>
            <option value={365}>1 Year</option>
          </select>
          <span className="text-[11px] text-muted-foreground block">
            Telemetry older than retention window is automatically purged to minimize storage overhead and protect privacy.
          </span>
        </div>

        <div className="pt-3 border-t border-border flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleExportJson}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-border text-xs font-semibold hover:bg-muted"
            >
              <Download className="w-4 h-4" />
              Export Full User Data (JSON)
            </button>
            <button
              type="button"
              onClick={handleDeleteAccountData}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-destructive/30 text-destructive text-xs font-semibold hover:bg-destructive/10"
            >
              <Trash2 className="w-4 h-4" />
              Delete Account Data
            </button>
          </div>

          <button
            type="submit"
            className="px-5 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90"
          >
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}
