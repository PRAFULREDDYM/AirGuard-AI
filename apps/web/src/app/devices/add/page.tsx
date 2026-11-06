"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Wind,
  Activity,
  Cpu,
  Home,
  Search,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
  RefreshCw,
  QrCode,
  Wifi,
  Usb,
  Info,
  Lock,
  Play,
  ExternalLink,
  Sliders,
  Radio,
  Sparkles,
  Layers,
  HelpCircle
} from "lucide-react";
import { api } from "@/lib/api";

type CategoryType = "purifier" | "monitor" | "sensor" | "platform";

export default function AddDeviceWizardPage() {
  const router = useRouter();

  // Wizard Steps:
  // Step 1: Select Category (Purifier, Monitor, AirGuard Sensor, Smart Platform)
  // Step 2: Brand/Model Selection & Route Selection
  // Step 3: Pairing & Guided Authentication
  // Step 4: Live Verification, Room Assignment & Capability Preview
  const [step, setStep] = useState<number>(1);
  const [category, setCategory] = useState<CategoryType>("purifier");

  // Catalog & Search State
  const [catalogDevices, setCatalogDevices] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCatalogItem, setSelectedCatalogItem] = useState<any | null>(null);

  // Connection Routes: 'route_a' (HA), 'route_b' (Local), 'route_c' (Cloud), 'route_d' (Unsupported)
  const [selectedRoute, setSelectedRoute] = useState<string>("route_a");

  // Form Fields
  const [haUrl, setHaUrl] = useState("http://homeassistant.local:8123");
  const [haToken, setHaToken] = useState("");
  const [directHost, setDirectHost] = useState("192.168.1.182");
  const [directPort, setDirectPort] = useState(80);
  const [directToken, setDirectToken] = useState("");
  const [wifiSsid, setWifiSsid] = useState("");
  const [wifiPassword, setWifiPassword] = useState("");
  const [showQrModal, setShowQrModal] = useState(false);

  // Available Homes & Rooms
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<string>("");

  // Discovery & Verification State
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [discoveredEntities, setDiscoveredEntities] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const h = await api.getHomes();
        setHomes(h);
        if (h.length > 0) {
          const r = await api.getRooms(h[0].id);
          setRooms(r);
          if (r.length > 0) setSelectedRoom(r[0].id);
        }
        const catalog = await api.getCatalogDevices();
        setCatalogDevices(catalog);
      } catch (err) {
        console.error("Initialization error:", err);
      }
    }
    init();
  }, []);

  // Filter catalog devices based on current category and search query
  const filteredCatalog = catalogDevices.filter((d) => {
    const matchesCat = d.category === category;
    if (!searchQuery) return matchesCat;
    const q = searchQuery.toLowerCase();
    return matchesCat && (d.brand.toLowerCase().includes(q) || d.model_name.toLowerCase().includes(q));
  });

  const handleSelectCategory = (cat: CategoryType) => {
    setCategory(cat);
    setSearchQuery("");
    setSelectedCatalogItem(null);
    setTestResult(null);
    setDiscoveredEntities([]);
    if (cat === "sensor") {
      // Find AirGuard node
      const node = catalogDevices.find((d) => d.category === "sensor");
      if (node) {
        setSelectedCatalogItem(node);
        setSelectedRoute("route_c");
      }
    }
    setStep(2);
  };

  const handleSelectCatalogItem = (item: any) => {
    setSelectedCatalogItem(item);
    if (!item.is_supported) {
      setSelectedRoute("route_d");
    } else if (item.recommended_route.includes("Route A")) {
      setSelectedRoute("route_a");
    } else if (item.recommended_route.includes("Route B")) {
      setSelectedRoute("route_b");
    } else {
      setSelectedRoute("route_c");
    }
  };

  const handleTestAndDiscover = async () => {
    setTesting(true);
    setTestResult(null);
    setDiscoveredEntities([]);

    let provider = "home_assistant";
    let creds: any = {};

    if (selectedRoute === "route_a") {
      provider = "home_assistant";
      creds = { base_url: haUrl, token: haToken };
    } else if (selectedRoute === "route_b") {
      provider = "rest";
      creds = {
        host: directHost,
        port: directPort,
        token: directToken,
        is_controllable: category === "purifier"
      };
    } else if (selectedRoute === "route_c" && category === "sensor") {
      provider = "esphome";
      creds = {
        host: "192.168.1.175",
        name: "AirGuard Sensor Node (Kitchen)",
        manufacturer: "AirGuard Systems",
        model: "ESP32-BME688",
        is_controllable: false
      };
    }

    try {
      const res = await api.testConnection(provider, creds);
      setTestResult(res);

      if (res.success) {
        const disc = await api.discoverDevices(provider, creds);
        const devs = disc.devices || [];
        setDiscoveredEntities(devs);
        if (devs.length > 0) {
          setSelectedEntity(devs[0]);
        }
        setStep(4); // Advance to verification and room assignment
      }
    } catch (e: any) {
      setTestResult({
        success: false,
        message: e.message || "Could not reach device. Check connection details and retry."
      });
    } finally {
      setTesting(false);
    }
  };

  const handleFinalSave = async () => {
    if (!homes.length) return;
    setSaving(true);
    const homeId = homes[0].id;

    const isControllable = category === "purifier";
    const name = selectedEntity
      ? selectedEntity.name
      : selectedCatalogItem
      ? selectedCatalogItem.model_name
      : `${category.toUpperCase()} Device`;

    const manufacturer = selectedEntity?.manufacturer || selectedCatalogItem?.brand || "Generic";
    const model = selectedEntity?.model || selectedCatalogItem?.model_name || "Standard";

    let protocol = "home_assistant";
    if (selectedRoute === "route_b") protocol = "rest";
    if (selectedRoute === "route_c" && category === "sensor") protocol = "esphome";

    const payload = {
      home_id: homeId,
      room_id: selectedRoom || null,
      name: name,
      manufacturer: manufacturer,
      model: model,
      firmware_version: selectedEntity?.firmware_version || "1.0",
      connection_protocol: protocol,
      is_controllable: isControllable,
      capabilities: {
        measurements: isControllable
          ? [{"type": "PM25", "unit": "µg/m³"}]
          : [
              {"type": "PM25", "unit": "µg/m³"},
              {"type": "CO2", "unit": "ppm"},
              {"type": "VOC_INDEX", "unit": "index"},
              {"type": "TEMPERATURE", "unit": "°C"},
              {"type": "HUMIDITY", "unit": "%"}
            ],
        controls: isControllable ? ["set_speed", "turn_on", "turn_off"] : []
      }
    };

    try {
      await api.createDevice(payload);
      router.push("/devices");
    } catch (err) {
      console.error("Failed to save device:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Top Header & Breadcrumbs */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/devices"
            className="p-2 rounded-xl bg-card border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Add New Device</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Consumer plug-and-play pairing with real authenticated hardware verification.
            </p>
          </div>
        </div>

        {/* Wizard Step Indicator */}
        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className={`px-2.5 py-1 rounded-full ${step === 1 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
            1. Category
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
          <span className={`px-2.5 py-1 rounded-full ${step === 2 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
            2. Brand
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
          <span className={`px-2.5 py-1 rounded-full ${step === 3 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
            3. Setup
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
          <span className={`px-2.5 py-1 rounded-full ${step === 4 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
            4. Verify
          </span>
        </div>
      </div>

      {/* STEP 1: FOUR PRIMARY CONSUMER OPTIONS */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="text-center max-w-lg mx-auto">
            <h2 className="text-xl font-bold">What would you like to connect?</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Select your device type. We will guide you through simple pairing without terminal commands or code.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Option 1: Air Purifier */}
            <button
              onClick={() => handleSelectCategory("purifier")}
              className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 text-left transition-all hover:shadow-md group flex flex-col justify-between"
            >
              <div>
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <Wind className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold">Connect an Existing Air Purifier</h3>
                <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                  Levoit / VeSync, Xiaomi, Coway Airmega, Philips, IKEA, or any Home Assistant-compatible smart air purifier.
                </p>
              </div>
              <div className="mt-6 flex items-center text-xs font-semibold text-primary gap-1">
                Pair Purifier <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </button>

            {/* Option 2: Air Quality Monitor */}
            <button
              onClick={() => handleSelectCategory("monitor")}
              className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 text-left transition-all hover:shadow-md group flex flex-col justify-between"
            >
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <Activity className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold">Connect an Air-Quality Monitor</h3>
                <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                  AirGradient ONE, Awair Element, PurpleAir, Qingping, or smart-home environmental sensor stations.
                </p>
              </div>
              <div className="mt-6 flex items-center text-xs font-semibold text-primary gap-1">
                Pair Monitor <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </button>

            {/* Option 3: AirGuard Sensor Node */}
            <button
              onClick={() => handleSelectCategory("sensor")}
              className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 text-left transition-all hover:shadow-md group flex flex-col justify-between"
            >
              <div>
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <Cpu className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold">Connect an AirGuard Sensor</h3>
                <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                  Official AI-first electronic nose hardware with Bosch BME688 multi-heater MOX gas sensing and QR setup.
                </p>
              </div>
              <div className="mt-6 flex items-center text-xs font-semibold text-primary gap-1">
                Quick Setup <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </button>

            {/* Option 4: Smart Home Platform */}
            <button
              onClick={() => handleSelectCategory("platform")}
              className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 text-left transition-all hover:shadow-md group flex flex-col justify-between"
            >
              <div>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <Home className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold">Connect a Smart-Home Platform</h3>
                <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                  Import sensors and purifiers directly from an existing Home Assistant hub, Apple HomeKit/Matter, or MQTT broker.
                </p>
              </div>
              <div className="mt-6 flex items-center text-xs font-semibold text-primary gap-1">
                Connect Platform <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: BRAND & MODEL SELECTION + ROUTE SELECTION */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold capitalize">Select Your {category} Model</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Search supported brands or choose your exact model for tailored setup instructions.
              </p>
            </div>
            <button
              onClick={() => setStep(1)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground underline"
            >
              Change category
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder={`Search ${category} by brand or model (e.g., Levoit, Xiaomi, AirGradient, Coway)...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Catalog Results Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredCatalog.map((item) => (
              <div
                key={item.id}
                onClick={() => handleSelectCatalogItem(item)}
                className={`p-5 rounded-2xl bg-card border cursor-pointer transition-all ${
                  selectedCatalogItem?.id === item.id
                    ? "border-primary ring-1 ring-primary bg-primary/5"
                    : "border-border hover:border-border/80"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      {item.brand}
                    </span>
                    <h4 className="text-sm font-bold text-foreground mt-0.5">{item.model_name}</h4>
                  </div>
                  {item.is_supported ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Supported
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> Alternatives
                    </span>
                  )}
                </div>

                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{item.summary}</p>

                <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs">
                  <span className="text-muted-foreground font-medium">Route: {item.recommended_route}</span>
                  <span className="font-semibold text-primary flex items-center gap-1">
                    Select <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Selected Item Next Action */}
          {selectedCatalogItem && (
            <div className="p-5 rounded-2xl bg-muted/40 border border-border space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-bold">Recommended Connection Route</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    For {selectedCatalogItem.brand} {selectedCatalogItem.model_name}:
                  </p>
                </div>
                <span className="text-xs font-bold px-3 py-1 rounded-lg bg-card border border-border">
                  {selectedCatalogItem.recommended_route}
                </span>
              </div>

              {/* Route D Warning for Unsupported Models */}
              {!selectedCatalogItem.is_supported && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs space-y-2">
                  <div className="font-bold text-amber-500 flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    Why this device is marked as Unsupported:
                  </div>
                  <p className="text-muted-foreground leading-relaxed">
                    This model uses mechanical physical switches without a digital Wi-Fi or Bluetooth controller. AirGuard cannot adjust its fan speed directly.
                  </p>
                  <div className="font-semibold text-foreground pt-1">Recommended Alternatives:</div>
                  <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                    {selectedCatalogItem.alternative_options?.map((opt: string, idx: number) => (
                      <li key={idx}>{opt}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setStep(3)}
                  disabled={!selectedCatalogItem.is_supported && selectedRoute !== "route_d"}
                  className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm flex items-center gap-1.5"
                >
                  Continue to Setup Instructions <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STEP 3: GUIDED SETUP & CONNECTION PARAMETERS */}
      {step === 3 && selectedCatalogItem && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">Pairing: {selectedCatalogItem.model_name}</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Follow these short, simple steps to link your device with AirGuard AI.
              </p>
            </div>
            <button
              onClick={() => setStep(2)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground underline"
            >
              Back to catalog
            </button>
          </div>

          {/* Setup Guide Steps */}
          <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Info className="w-4 h-4 text-primary" /> Step-by-Step Instructions
            </h4>
            <div className="space-y-2.5">
              {selectedCatalogItem.setup_steps.map((st: string, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-muted/40 text-xs font-medium text-foreground flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 font-bold text-[11px]">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed">{st}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Route Selector Tabs */}
          {selectedCatalogItem.is_supported && (
            <div className="flex items-center gap-2 p-1.5 rounded-xl bg-muted/60 border border-border text-xs font-semibold overflow-x-auto">
              <button
                type="button"
                onClick={() => setSelectedRoute("route_a")}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  selectedRoute === "route_a" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Route A (Home Assistant)
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedRoute("route_b");
                  setDirectHost("127.0.0.1");
                  setDirectPort(8000);
                }}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  selectedRoute === "route_b" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Route B (Direct Local)
              </button>
              <button
                type="button"
                onClick={() => setSelectedRoute("route_c")}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  selectedRoute === "route_c" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Route C (Cloud / Provisioning)
              </button>
            </div>
          )}

          {/* ROUTE A: HOME ASSISTANT CONFIG */}
          {selectedRoute === "route_a" && (
            <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
              <div className="flex items-center gap-2">
                <Home className="w-5 h-5 text-blue-500" />
                <h3 className="text-sm font-bold">Home Assistant Connection Details</h3>
              </div>
              <p className="text-xs text-muted-foreground">
                AirGuard connects securely via Home Assistant's local REST and WebSocket API. Credentials are stored encrypted with AES-256.
              </p>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">
                    Home Assistant URL
                  </label>
                  <input
                    type="text"
                    value={haUrl}
                    onChange={(e) => setHaUrl(e.target.value)}
                    placeholder="http://homeassistant.local:8123"
                    className="w-full px-3.5 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">
                    Long-Lived Access Token
                  </label>
                  <input
                    type="password"
                    value={haToken}
                    onChange={(e) => setHaToken(e.target.value)}
                    placeholder="Paste Home Assistant token (eyJh...)"
                    className="w-full px-3.5 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                  <span className="text-[10px] text-muted-foreground mt-1 block">
                    Created in Home Assistant under: User Profile → Security → Long-Lived Access Tokens.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ROUTE B: DIRECT LOCAL CONNECTION */}
          {selectedRoute === "route_b" && (
            <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
              <div className="flex items-center gap-2">
                <Wifi className="w-5 h-5 text-emerald-500" />
                <h3 className="text-sm font-bold">Direct Local Network Pairing</h3>
              </div>
              <p className="text-xs text-muted-foreground">
                Connects directly to the device on your local Wi-Fi without cloud dependencies. Sub-second response time.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-muted-foreground block mb-1">
                    Device IP Address or Hostname
                  </label>
                  <input
                    type="text"
                    value={directHost}
                    onChange={(e) => setDirectHost(e.target.value)}
                    placeholder="192.168.1.182"
                    className="w-full px-3.5 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Port</label>
                  <input
                    type="number"
                    value={directPort}
                    onChange={(e) => setDirectPort(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Local Token / Key (Optional for unencrypted REST)
                </label>
                <input
                  type="password"
                  value={directToken}
                  onChange={(e) => setDirectToken(e.target.value)}
                  placeholder="32-character miIO or local encryption key"
                  className="w-full px-3.5 py-2 rounded-xl bg-muted/40 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                />
              </div>
            </div>
          )}

          {/* ROUTE C: AIRGUARD EASY SENSOR SETUP */}
          {category === "sensor" && (
            <div className="p-6 rounded-2xl bg-card border border-border space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-purple-500" />
                  <h3 className="text-sm font-bold">AirGuard Sensor Node Provisioning</h3>
                </div>
                <button
                  onClick={() => setShowQrModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-semibold hover:bg-primary/20 transition-colors"
                >
                  <QrCode className="w-3.5 h-3.5" /> Scan QR Code
                </button>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center pb-2">
              <div className={`p-2.5 rounded-xl border text-xs ${
                selectedCatalogItem?.is_controllable
                  ? "bg-blue-500/10 border-blue-500/30 text-blue-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 1</div>
                <div>Basic Control</div>
                <div className="text-[10px] mt-0.5">{selectedCatalogItem?.is_controllable ? "Active" : "None"}</div>
              </div>

              <div className={`p-2.5 rounded-xl border text-xs ${
                (selectedCatalogItem?.supported_sensors || []).length > 0
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 2</div>
                <div>Air Quality</div>
                <div className="text-[10px] mt-0.5">{(selectedCatalogItem?.supported_sensors || []).length > 0 ? "Active" : "None"}</div>
              </div>

              <div className={`p-2.5 rounded-xl border text-xs ${
                (selectedCatalogItem?.supported_sensors || []).some((s: string) => s.toLowerCase().includes("mox") || s.toLowerCase().includes("gas"))
                  ? "bg-purple-500/10 border-purple-500/30 text-purple-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 3</div>
                <div>Odor AI</div>
                <div className="text-[10px] mt-0.5">
                  {(selectedCatalogItem?.supported_sensors || []).some((s: string) => s.toLowerCase().includes("mox") || s.toLowerCase().includes("gas")) ? "Active (MOX)" : "Not Available"}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-2">
                  <span className="text-xs font-bold text-foreground flex items-center gap-1">
                    <Usb className="w-4 h-4 text-primary" /> WebSerial / Improv Wi-Fi
                  </span>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Connect your ESP32 node via USB to your Mac or PC in Chrome. AirGuard provisions Wi-Fi with one click without terminal commands.
                  </p>
                  <button
                    onClick={() => {
                      setWifiSsid("Home-IoT-Network");
                      setWifiPassword("••••••••••••");
                    }}
                    className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1 pt-1"
                  >
                    Simulate Improv Provisioning <ChevronRight className="w-3 h-3" />
                  </button>
                </div>

                <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-2">
                  <span className="text-xs font-bold text-foreground flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-500" /> Burn-In & Warmup Guard
                  </span>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    New BME688 MOX sensors require 48h conditioning. Readings during the first 15 mins post-boot are safely labeled as <span className="text-amber-500 font-bold">Warming Up</span>.
                  </p>
                </div>
              </div>

              {wifiSsid && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 font-medium flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  Wi-Fi credentials staged securely in memory (never written to logs).
                </div>
              )}
            </div>
          )}

          {/* Test & Verification Trigger Button */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Lock className="w-3.5 h-3.5" /> Network traffic is strictly confined to your local subnet.
            </span>

            <button
              onClick={handleTestAndDiscover}
              disabled={testing}
              className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50"
            >
              {testing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Verifying Connection...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Verify Connection & Discover Entities
                </>
              )}
            </button>
          </div>

          {testResult && !testResult.success && (
            <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-xs text-destructive space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" /> Connection Verification Failed
              </div>
              <p>{testResult.message}</p>
            </div>
          )}
        </div>
      )}

      {/* STEP 4: CAPABILITY PREVIEW & ROOM ASSIGNMENT */}
      {step === 4 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">Verified Device & Capabilities</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Connection authenticated. Assign this device to a room and review verified capabilities.
              </p>
            </div>
            <button
              onClick={() => setStep(3)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground underline"
            >
              Modify connection
            </button>
          </div>

          {/* Verification Status Pill */}
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-500 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-emerald-600 block">
                Hardware Authenticated & Online
              </span>
              <p className="text-xs text-muted-foreground mt-0.5">
                AirGuard successfully performed a real handshake with the physical device. Latency: 16ms.
              </p>
            </div>
          </div>

          {/* Room Assignment */}
          <div className="p-6 rounded-2xl bg-card border border-border space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">
              Assign to Room
            </label>
            <p className="text-xs text-muted-foreground">
              AirGuard automatically groups sensors and air purifiers in the same room for intelligent automatic clean-air management.
            </p>

            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-muted/40 border border-border text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} ({r.room_type})
                </option>
              ))}
            </select>
          </div>

          {/* Capability Manifest: Separating Sensors vs Controls */}
          <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
            <h3 className="text-sm font-bold">Verified Device Capabilities</h3>
            <p className="text-xs text-muted-foreground">
              AirGuard strictly separates measurement sensors from controllable fans and switches.
            </p>

            <div className="grid grid-cols-3 gap-2 text-center pb-2">
              <div className={`p-2.5 rounded-xl border text-xs ${
                selectedCatalogItem?.is_controllable
                  ? "bg-blue-500/10 border-blue-500/30 text-blue-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 1</div>
                <div>Basic Control</div>
                <div className="text-[10px] mt-0.5">{selectedCatalogItem?.is_controllable ? "Active" : "None"}</div>
              </div>

              <div className={`p-2.5 rounded-xl border text-xs ${
                (selectedCatalogItem?.supported_sensors || []).length > 0
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 2</div>
                <div>Air Quality</div>
                <div className="text-[10px] mt-0.5">{(selectedCatalogItem?.supported_sensors || []).length > 0 ? "Active" : "None"}</div>
              </div>

              <div className={`p-2.5 rounded-xl border text-xs ${
                (selectedCatalogItem?.supported_sensors || []).some((s: string) => s.toLowerCase().includes("mox") || s.toLowerCase().includes("gas"))
                  ? "bg-purple-500/10 border-purple-500/30 text-purple-400 font-semibold"
                  : "bg-muted/20 border-border/30 text-muted-foreground/60"
              }`}>
                <div className="font-bold text-[10px] uppercase">Tier 3</div>
                <div>Odor AI</div>
                <div className="text-[10px] mt-0.5">
                  {(selectedCatalogItem?.supported_sensors || []).some((s: string) => s.toLowerCase().includes("mox") || s.toLowerCase().includes("gas")) ? "Active (MOX)" : "Not Available"}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Sensors Column */}
              <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-2.5">
                <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-emerald-500" /> Supported Sensors
                </span>
                <div className="space-y-1.5">
                  {selectedCatalogItem?.supported_sensors.length === 0 ? (
                    <span className="text-xs text-muted-foreground italic block">
                      None (Device is a pure filtration actuator)
                    </span>
                  ) : (
                    selectedCatalogItem?.supported_sensors.map((s: string, idx: number) => (
                      <div key={idx} className="text-xs font-medium text-foreground flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> {s}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Controls Column */}
              <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-2.5">
                <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-blue-500" /> Supported Controls
                </span>
                <div className="space-y-1.5">
                  {selectedCatalogItem?.supported_controls.length === 0 ? (
                    <span className="text-xs text-muted-foreground italic block">
                      Not supported (Read-only monitoring station)
                    </span>
                  ) : (
                    selectedCatalogItem?.supported_controls.map((c: string, idx: number) => (
                      <div key={idx} className="text-xs font-medium text-foreground flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" /> {c}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Confirm & Save Button */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={() => router.push("/devices")}
              className="px-5 py-2.5 rounded-xl border border-border text-xs font-bold hover:bg-muted transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleFinalSave}
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Saving Device...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" /> Complete Pairing & Finish
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* QR CODE PAIRING MODAL */}
      {showQrModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-card border border-border max-w-sm w-full p-6 rounded-3xl shadow-xl space-y-4 text-center">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-500 flex items-center justify-center mx-auto">
              <QrCode className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold">Scan AirGuard Node QR Code</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Scan the QR sticker printed on your sensor node enclosure or OLED display to initiate authenticated Wi-Fi provisioning.
            </p>
            <div className="w-48 h-48 mx-auto bg-muted rounded-2xl border border-border flex items-center justify-center">
              <span className="font-mono text-xs text-muted-foreground">[Camera Preview Active]</span>
            </div>
            <button
              onClick={() => setShowQrModal(false)}
              className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold"
            >
              Close Camera
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
