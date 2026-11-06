"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import "./globals.css";
import {
  LayoutDashboard,
  Home as HomeIcon,
  Cpu,
  AlertTriangle,
  Zap,
  FlaskConical,
  BarChart3,
  Settings as SettingsIcon,
  Activity,
  ShieldCheck,
  Radio,
  Sun,
  Moon,
  Plus
} from "lucide-react";
import { api } from "@/lib/api";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isDark, setIsDark] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [activeScenario, setActiveScenario] = useState("normal");

  useEffect(() => {
    // Check initial dark mode
    if (typeof window !== "undefined") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setIsDark(prefersDark);
      if (prefersDark) document.documentElement.classList.add("dark");
    }

    // Connect WebSocket
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws";
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
    } catch (e) {
      console.warn("WebSocket connection error:", e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const navItems = [
    { label: "Overview", href: "/", icon: LayoutDashboard },
    { label: "Rooms", href: "/rooms", icon: HomeIcon },
    { label: "Devices", href: "/devices", icon: Cpu },
    { label: "Events & Alerts", href: "/events", icon: AlertTriangle },
    { label: "Automations", href: "/automations", icon: Zap },
    { label: "AI Model Lab", href: "/models", icon: FlaskConical },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Settings", href: "/settings", icon: SettingsIcon },
  ];

  return (
    <html lang="en">
      <head>
        <title>AirGuard AI — Environmental Sensing & Odor Intelligence</title>
        <meta name="description" content="AI-powered air quality monitoring, odor recognition, and smart device automation" />
      </head>
      <body className="min-h-screen bg-background text-foreground flex flex-col md:flex-row antialiased">
        {/* Sidebar Nav */}
        <aside className="w-full md:w-64 bg-card border-r border-border flex flex-col justify-between shrink-0">
          <div>
            {/* Brand Logo */}
            <div className="p-5 border-b border-border flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-md shadow-primary/20">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <span className="font-bold text-lg tracking-tight block leading-tight">AirGuard AI</span>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-widest block font-medium">Environmental AI</span>
                </div>
              </Link>
            </div>

            {/* Nav Links */}
            <nav className="p-3 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Bottom status widgets */}
          <div className="p-4 border-t border-border space-y-3">
            {/* Live WebSocket Status */}
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/60 text-xs">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
                <span className="font-medium text-muted-foreground">
                  {wsConnected ? "Live Telemetry" : "Polling Active"}
                </span>
              </div>
              <Radio className="w-3.5 h-3.5 text-muted-foreground" />
            </div>

            {/* Non-negotiable safety badge */}
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground bg-muted/40 p-2 rounded-lg">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span>Safety Engine Active: Hazard-safe rules enforced.</span>
            </div>

            {/* Theme Toggle Button */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-xs text-muted-foreground">Appearance</span>
              <button
                onClick={toggleTheme}
                aria-label="Toggle theme"
                className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-y-auto min-h-screen">
          {/* Top Banner indicating Simulation Mode */}
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-700 dark:text-amber-300">
            <div className="flex items-center gap-2">
              <span className="font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-[10px]">
                Simulation Adapter Available
              </span>
              <span>Synthetic readings are unmistakably labeled. Real hardware adapters connect via Devices menu.</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Test Scenario:</span>
              <button
                onClick={async () => {
                  setActiveScenario("normal");
                  await api.triggerSimulationTick("normal");
                }}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  activeScenario === "normal" ? "bg-amber-500 text-white" : "bg-card border border-amber-500/30 hover:bg-muted"
                }`}
              >
                Normal
              </button>
              <button
                onClick={async () => {
                  setActiveScenario("cooking");
                  await api.triggerSimulationTick("cooking");
                }}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  activeScenario === "cooking" ? "bg-amber-500 text-white" : "bg-card border border-amber-500/30 hover:bg-muted"
                }`}
              >
                Cooking Event (PM2.5 ↑)
              </button>
              <button
                onClick={async () => {
                  setActiveScenario("cleaning");
                  await api.triggerSimulationTick("cleaning");
                }}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  activeScenario === "cleaning" ? "bg-amber-500 text-white" : "bg-card border border-amber-500/30 hover:bg-muted"
                }`}
              >
                Cleaning Event (VOC ↑)
              </button>
            </div>
          </div>

          <div className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}

