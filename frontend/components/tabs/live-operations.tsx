"use client";

import React, { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import {
  AlertTriangle,
  ChevronRight,
  Copy,
  Crosshair,
  Loader2,
  MapPin,
  Radio,
  Shield,
  Truck,
  Users,
  Zap,
  Check,
  Construction,
  TriangleAlert,
  Route,
  Siren,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

// Dynamically import LeafletMap to avoid SSR issues
const LeafletMap = dynamic(
  () => import("@/components/ui/leaflet-map").then((mod) => mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[360px] rounded-lg bg-background/50 border border-border/30 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    ),
  }
);

// ── Constants ──
const EVENT_CAUSES = [
  { value: "accident", label: "Accident" },
  { value: "water_logging", label: "Water Logging" },
  { value: "vehicle_breakdown", label: "Vehicle Breakdown" },
  { value: "vip_movement", label: "VIP Movement" },
  { value: "public_event", label: "Public Event / Rally" },
  { value: "construction", label: "Construction / Metro Work" },
];

const VEHICLE_TYPES = [
  { value: "car", label: "Car / Sedan" },
  { value: "suv", label: "SUV / MUV" },
  { value: "truck", label: "Truck / Lorry" },
  { value: "bus", label: "Bus" },
];

interface Props {
  onIncidentCountChange?: (count: number) => void;
}

export function LiveOperationsTab({ onIncidentCountChange }: Props) {
  // ── Map & Geo state ──
  const [latitude, setLatitude] = useState(12.9716);
  const [longitude, setLongitude] = useState(77.5946);
  const [centroids, setCentroids] = useState<Array<{ lat: number; lng: number; name: string }>>([]);

  // ── Geo-context resolution ──
  const [corridor, setCorridor] = useState("");
  const [zone, setZone] = useState("");
  const [policeStation, setPoliceStation] = useState("");
  const [geoConfidence, setGeoConfidence] = useState("");
  const [isResolvingGeo, setIsResolvingGeo] = useState(false);
  const [geoError, setGeoError] = useState(false);

  // ── Intake form (Time-Zero inputs only) ──
  const [eventCause, setEventCause] = useState("accident");
  const [vehicleType, setVehicleType] = useState("car");
  const [eventType, setEventType] = useState("unplanned"); // planned / unplanned
  const [eventTime, setEventTime] = useState("");

  // ── Prediction state ──
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [isLoadingPredict, setIsLoadingPredict] = useState(false);
  const [copied, setCopied] = useState(false);

  // ── Active incidents list (for MLOps tab cross-reference) ──
  const [incidents, setIncidents] = useState<Array<{
    id: string;
    location: string;
    severity: string;
    cause: string;
    timestamp: string;
    manpower: number;
  }>>([]);

  // ── Init ──
  useEffect(() => {
    // Set default event time to now
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    setEventTime(now.toISOString().slice(0, 16));

    // Load centroids from Supabase
    fetch("http://127.0.0.1:8000/api/centroids")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCentroids(data.map((c: any) => ({
            lat: c.centroid_lat,
            lng: c.centroid_lng,
            name: `Cluster ${c.cluster_id}`,
          })));
        }
      })
      .catch((err) => console.error("Failed to load centroids:", err));
  }, []);

  // ── Geo-context resolver ──
  const resolveGeoContext = useCallback(async (lat: number, lng: number) => {
    setIsResolvingGeo(true);
    setGeoError(false);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/geo-context?lat=${lat}&lng=${lng}`);
      if (res.ok) {
        const data = await res.json();
        setCorridor(data.corridor || "Non-corridor");
        setZone(data.zone || "Unknown");
        setPoliceStation(data.police_station || "Unknown");
        setGeoConfidence(data.confidence || "Low");
      } else {
        setGeoError(true);
      }
    } catch {
      setGeoError(true);
    } finally {
      setIsResolvingGeo(false);
    }
  }, []);

  // ── Map click handler ──
  const handleMapClick = useCallback((lat: number, lng: number) => {
    setLatitude(lat);
    setLongitude(lng);
    setPredictionResult(null);
    resolveGeoContext(lat, lng);
  }, [resolveGeoContext]);

  // ── Generate AI Strategy ──
  const handlePredict = async () => {
    if (!corridor || geoError) {
      alert("Drop a pin on the map first to resolve location context.");
      return;
    }
    setIsLoadingPredict(true);
    setPredictionResult(null);
    try {
      const payload = {
        latitude,
        longitude,
        event_cause: eventCause,
        priority: "High", // auto-determined by model, not user input
        requires_road_closure: false, // model infers this
        corridor,
        zone,
        police_station: policeStation,
        event_time: new Date(eventTime).toISOString(),
        event_type: eventType,
      };

      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setPredictionResult(data);

        // Add to active incidents
        const newIncident = {
          id: `EVT-${Date.now().toString(36).toUpperCase().slice(-6)}`,
          location: `${corridor} @ ${policeStation}`,
          severity: data.prediction.impact_severity,
          cause: eventCause.replace("_", " "),
          timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false }),
          manpower: data.recommendations.manpower,
        };
        setIncidents(prev => {
          const updated = [newIncident, ...prev];
          onIncidentCountChange?.(updated.length);
          return updated;
        });
      } else {
        alert("Prediction failed: " + (await res.text()));
      }
    } catch (err) {
      console.error("Predict error:", err);
      alert("Backend API is not responding. Make sure the FastAPI server is running.");
    } finally {
      setIsLoadingPredict(false);
    }
  };

  // ── Copy dispatch script ──
  const copyScript = () => {
    if (!predictionResult?.llm_dispatch_script) return;
    navigator.clipboard.writeText(predictionResult.llm_dispatch_script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Severity color helper ──
  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case "HIGH": return { color: "text-severity-high", bg: "bg-severity-high/15", border: "border-severity-high/40", glow: "severity-glow-high" };
      case "MEDIUM": return { color: "text-severity-medium", bg: "bg-severity-medium/15", border: "border-severity-medium/40", glow: "severity-glow-medium" };
      default: return { color: "text-severity-low", bg: "bg-severity-low/15", border: "border-severity-low/40", glow: "" };
    }
  };

  const severity = predictionResult?.prediction?.impact_severity || "";
  const sevStyle = getSeverityStyle(severity);

  return (
    <div className="flex h-full">
      {/* ══════════════ LEFT PANE: Context Zone ══════════════ */}
      <div className="w-[50%] flex-shrink-0 border-r border-border/30 p-5 overflow-y-auto space-y-4">
        {/* Section Header */}
        <div className="flex items-center gap-2 mb-1">
          <Crosshair className="w-4 h-4 text-accent-cyan" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Context Zone — Inputs
          </h2>
        </div>

        {/* Interactive Map */}
        <LeafletMap
          latitude={latitude}
          longitude={longitude}
          onMapClick={handleMapClick}
          centroids={centroids}
        />

        {/* Geo-context status bar */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-md bg-accent/30 border border-border/30">
          {isResolvingGeo ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-accent-cyan" />
              <span className="text-xs font-mono text-muted-foreground">Resolving location context…</span>
            </>
          ) : geoError ? (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-severity-high" />
              <span className="text-xs font-mono text-severity-high">Geo-context lookup failed</span>
            </>
          ) : corridor ? (
            <>
              <MapPin className="w-3.5 h-3.5 text-accent-cyan" />
              <span className="text-xs font-mono text-foreground/80">
                {corridor} · {zone} · {policeStation}
              </span>
              <Badge variant="outline" className={`ml-auto text-[10px] font-mono ${geoConfidence === "High" ? "bg-severity-low/15 text-severity-low border-severity-low/30" : geoConfidence === "Medium" ? "bg-severity-medium/15 text-severity-medium border-severity-medium/30" : "bg-muted text-muted-foreground border-border"}`}>
                {geoConfidence} Confidence
              </Badge>
            </>
          ) : (
            <>
              <MapPin className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-mono text-muted-foreground">Click map to select incident location</span>
            </>
          )}
        </div>

        <Separator className="my-1" />

        {/* ── Intake Form ── */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {/* Event Cause */}
            <div className="space-y-1.5">
              <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                Event Cause
              </Label>
              <Select value={eventCause} onValueChange={(val) => setEventCause(val || "accident")}>
                <SelectTrigger className="bg-accent/30 border-border/40 text-sm h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_CAUSES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Vehicle Type — only shown for breakdowns */}
            <div className="space-y-1.5">
              <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                {eventCause === "vehicle_breakdown" ? "Vehicle Type" : "Event Type"}
              </Label>
              {eventCause === "vehicle_breakdown" ? (
                <Select value={vehicleType} onValueChange={(val) => setVehicleType(val || "car")}>
                  <SelectTrigger className="bg-accent/30 border-border/40 text-sm h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VEHICLE_TYPES.map((v) => (
                      <SelectItem key={v.value} value={v.value}>{v.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="flex items-center gap-3 h-9 px-3 rounded-md bg-accent/30 border border-border/40">
                  <Label className={`text-xs cursor-pointer ${eventType === "unplanned" ? "text-foreground" : "text-muted-foreground"}`}>
                    Unplanned
                  </Label>
                  <Switch
                    checked={eventType === "planned"}
                    onCheckedChange={(checked) => setEventType(checked ? "planned" : "unplanned")}
                    className="data-[state=checked]:bg-accent-violet"
                  />
                  <Label className={`text-xs cursor-pointer ${eventType === "planned" ? "text-foreground" : "text-muted-foreground"}`}>
                    Planned
                  </Label>
                </div>
              )}
            </div>
          </div>

          {/* Event Dispatch Time */}
          <div className="space-y-1.5">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
              Event Dispatch Time
            </Label>
            <Input
              type="datetime-local"
              value={eventTime}
              onChange={(e) => setEventTime(e.target.value)}
              className="bg-accent/30 border-border/40 text-sm h-9 font-mono"
            />
          </div>

          {/* Lat/Lng display (auto-filled, read-only) */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground/60">Latitude</Label>
              <Input value={latitude.toFixed(6)} readOnly className="bg-accent/20 border-border/30 text-xs h-8 font-mono text-muted-foreground" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground/60">Longitude</Label>
              <Input value={longitude.toFixed(6)} readOnly className="bg-accent/20 border-border/30 text-xs h-8 font-mono text-muted-foreground" />
            </div>
          </div>
        </div>

        {/* ── ACTION BUTTON ── */}
        <Button
          onClick={handlePredict}
          disabled={isLoadingPredict || !corridor || geoError}
          size="lg"
          className="w-full h-14 text-base font-bold bg-gradient-to-r from-accent-blue via-accent-violet to-accent-blue bg-[length:200%_auto] hover:bg-right transition-all duration-500 text-white cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoadingPredict ? (
            <>
              <Loader2 className="w-5 h-5 mr-3 animate-spin" />
              Running AI Inference…
            </>
          ) : (
            <>
              <Zap className="w-5 h-5 mr-3" />
              Generate AI Strategy
            </>
          )}
        </Button>
      </div>

      {/* ══════════════ RIGHT PANE: Intelligence Zone ══════════════ */}
      <div className={`flex-1 p-5 overflow-y-auto space-y-4 ${!predictionResult ? "zone-dimmed" : "zone-active"}`}>
        {/* Section Header */}
        <div className="flex items-center gap-2 mb-1">
          <Shield className="w-4 h-4 text-accent-violet" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Intelligence Zone — AI Outputs
          </h2>
        </div>

        {!predictionResult ? (
          <div className="flex flex-col items-center justify-center h-[70%] text-center">
            <div className="w-20 h-20 rounded-full bg-accent/20 border border-border/30 flex items-center justify-center mb-4">
              <Shield className="w-10 h-10 text-muted-foreground/30" />
            </div>
            <p className="text-sm text-muted-foreground font-mono">AI Intelligence Standby</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Select a location and generate strategy to activate</p>
          </div>
        ) : (
          <>
            {/* ── Card 1: Prediction Engine ── */}
            <Card className={`glass-card ${sevStyle.border} relative overflow-hidden`}>
              <div className={`absolute inset-0 ${sevStyle.bg} opacity-30`} />
              <CardContent className="p-6 relative">
                <div className="flex items-center gap-2 mb-2">
                  <TriangleAlert className={`w-4 h-4 ${sevStyle.color}`} />
                  <span className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                    Prediction Engine
                  </span>
                </div>
                <p className={`text-5xl font-black tracking-tight ${sevStyle.color} ${sevStyle.glow}`}>
                  {severity} IMPACT
                </p>
                <div className="flex items-center gap-4 mt-3 text-xs font-mono text-muted-foreground">
                  <span>Spatial Cluster: <span className="text-foreground">{predictionResult.metadata?.geo_cluster}</span></span>
                  <span className="text-border">·</span>
                  <span>Corridor Cascades (24h): <span className="text-foreground">{predictionResult.metadata?.cascading_events_24h}</span></span>
                  <span className="text-border">·</span>
                  <span>Confidence: <span className="text-foreground">{predictionResult.metadata?.confidence || "—"}</span></span>
                </div>
              </CardContent>
            </Card>

            {/* ── Card 2: Operational Checklist ── */}
            <Card className="glass-card border-border/50">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Construction className="w-4 h-4 text-accent-cyan" />
                  <CardTitle className="text-sm font-semibold">Operational Checklist</CardTitle>
                </div>
                <CardDescription className="text-[11px]">AI-generated resource allocation from heuristics engine</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  {/* Manpower */}
                  <div className="p-3 rounded-lg bg-accent/30 border border-border/30 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-blue/15 flex items-center justify-center">
                      <Users className="w-5 h-5 text-accent-blue" />
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase text-muted-foreground">Manpower</p>
                      <p className="text-2xl font-bold text-foreground">{predictionResult.recommendations?.manpower}</p>
                    </div>
                  </div>

                  {/* Barricades */}
                  <div className="p-3 rounded-lg bg-accent/30 border border-border/30 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-severity-medium/15 flex items-center justify-center">
                      <Construction className="w-5 h-5 text-severity-medium" />
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase text-muted-foreground">Barricades</p>
                      <p className="text-2xl font-bold text-foreground">{predictionResult.recommendations?.barricades}</p>
                    </div>
                  </div>

                  {/* Diversion Strategy */}
                  <div className="p-3 rounded-lg bg-accent/30 border border-border/30 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-violet/15 flex items-center justify-center">
                      <Route className="w-5 h-5 text-accent-violet" />
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase text-muted-foreground">Diversion</p>
                      <p className="text-sm font-semibold text-foreground">{predictionResult.recommendations?.diversion_level || "None"}</p>
                    </div>
                  </div>

                  {/* Special Equipment */}
                  <div className={`p-3 rounded-lg border flex items-center gap-3 ${predictionResult.recommendations?.special_equipment?.includes("Tow Truck") ? "bg-severity-high/10 border-severity-high/30" : "bg-accent/30 border-border/30"}`}>
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${predictionResult.recommendations?.special_equipment?.includes("Tow Truck") ? "bg-severity-high/20" : "bg-accent-cyan/15"}`}>
                      <Truck className={`w-5 h-5 ${predictionResult.recommendations?.special_equipment?.includes("Tow Truck") ? "text-severity-high" : "text-accent-cyan"}`} />
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase text-muted-foreground">Special Equipment</p>
                      <p className={`text-sm font-bold ${predictionResult.recommendations?.special_equipment?.includes("Tow Truck") ? "text-severity-high" : "text-foreground"}`}>
                        {predictionResult.recommendations?.special_equipment || "None"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* VMS Alert Badge */}
                {predictionResult.recommendations?.vms_alert && (
                  <div className="mt-3 px-3 py-2 rounded-md bg-severity-medium/10 border border-severity-medium/30 flex items-center gap-2">
                    <Siren className="w-4 h-4 text-severity-medium" />
                    <span className="text-xs font-mono text-severity-medium">VMS ALERT ACTIVATED — Variable Message Signs will broadcast to motorists</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ── Card 3: LLM Comm-Link ── */}
            <Card className="glass-card border-accent-blue/20">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Radio className="w-4 h-4 text-accent-blue" />
                    <CardTitle className="text-sm font-semibold">LLM Comm-Link — Radio Dispatch Script</CardTitle>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyScript}
                    className="h-7 text-xs font-mono gap-1.5 cursor-pointer border-accent-blue/30 hover:bg-accent-blue/10"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-severity-low" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        Copy to Radio Terminal
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="radio-transcript whitespace-pre-wrap">
                  {predictionResult.llm_dispatch_script || "No dispatch script generated."}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
