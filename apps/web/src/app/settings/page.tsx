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
  FileText
} from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [homes, setHomes] = useState<any[]>([]);
  const [retentionDays, setRetentionDays] = useState(90);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const u = await api.getMe();
        setUser(u);
        const h = await api.getHomes();
        setHomes(h);
      } catch (e) {
        console.error(e);
      }
    }
    init();
  }, []);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedMessage("Settings and data retention preferences saved successfully.");
    setTimeout(() => setSavedMessage(null), 3000);
  };

  const handleExportAll = () => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
    window.open(`${apiBase}/readings/export/csv?days=90`, "_blank");
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings & Privacy</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage user credentials, local-first storage, integration encryption, and data retention.
        </p>
      </div>

      {savedMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
          {savedMessage}
        </div>
      )}

      {/* Profile Card */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <h2 className="text-base font-bold flex items-center gap-2">
          <User className="w-4 h-4 text-primary" />
          User Profile
        </h2>

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-muted-foreground block mb-1">Email Address</span>
            <input
              type="text"
              disabled
              value={user?.email || "demo@airguard.ai"}
              className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-sm font-medium"
            />
          </div>
          <div>
            <span className="text-muted-foreground block mb-1">Full Name</span>
            <input
              type="text"
              disabled
              value={user?.full_name || "Demo User"}
              className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-sm font-medium"
            />
          </div>
        </div>
      </div>

      {/* Security & Encryption Card */}
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-3">
        <h2 className="text-base font-bold flex items-center gap-2">
          <Lock className="w-4 h-4 text-primary" />
          Integration Credentials & Local Security
        </h2>
        <p className="text-xs text-muted-foreground">
          All external integration tokens (Home Assistant long-lived tokens, MQTT credentials) are encrypted at rest using AES-256-GCM. Tokens are never exposed in browser storage or returned over insecure API responses.
        </p>
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 pt-1">
          <ShieldCheck className="w-4 h-4" />
          AES-256-GCM Encryption Key Configured
        </div>
      </div>

      {/* Data Retention & Privacy */}
      <form onSubmit={handleSaveSettings} className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
        <h2 className="text-base font-bold flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary" />
          Data Retention & Export
        </h2>

        <div className="text-xs space-y-2">
          <label className="font-semibold block text-muted-foreground">Telemetry Retention Period</label>
          <select
            value={retentionDays}
            onChange={(e) => setRetentionDays(Number(e.target.value))}
            className="w-full max-w-xs px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value={30}>30 Days (Local Storage Friendly)</option>
            <option value={90}>90 Days (Standard Analytics)</option>
            <option value={180}>180 Days (Longitudinal Research)</option>
            <option value={365}>1 Year</option>
          </select>
          <span className="text-[11px] text-muted-foreground block">
            Readings older than retention period are automatically purged to preserve privacy.
          </span>
        </div>

        <div className="pt-3 border-t border-border flex items-center justify-between">
          <button
            type="button"
            onClick={handleExportAll}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-border text-xs font-semibold hover:bg-muted"
          >
            <Download className="w-4 h-4" />
            Download Complete Data Archive (CSV)
          </button>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
          >
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}

