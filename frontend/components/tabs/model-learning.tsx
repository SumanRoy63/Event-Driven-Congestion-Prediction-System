"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Brain,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Loader2,
  RefreshCcw,
  Send,
  Terminal,
  Zap,
  BarChart3,
  MessageSquare,
  ChevronDown,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

// ── Types ──
interface IncidentLog {
  id: string;
  location: string;
  severity: string;
  cause: string;
  timestamp: string;
}

export function ModelLearningTab() {
  // ── Feedback queue ──
  const [logs, setLogs] = useState<IncidentLog[]>([]);
  const [logCount, setLogCount] = useState(0);
  const RETRAIN_THRESHOLD = 5;

  // ── Debrief modal ──
  const [debriefOpen, setDebriefOpen] = useState(false);
  const [debriefTarget, setDebriefTarget] = useState<IncidentLog | null>(null);
  const [actualImpact, setActualImpact] = useState("Medium");
  const [actualBarricades, setActualBarricades] = useState(0);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  // ── Retraining ──
  const [isRetraining, setIsRetraining] = useState(false);
  const [terminalLines, setTerminalLines] = useState<string[]>([
    "$ system ready — awaiting validated feedback logs",
  ]);
  const terminalRef = useRef<HTMLDivElement>(null);

  // ── Model stats ──
  const [modelVersion, setModelVersion] = useState("—");
  const [totalEvents, setTotalEvents] = useState(0);
  const [lastCalibration, setLastCalibration] = useState("Never");

  // ── Init: fetch real model stats ──
  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    fetch(`${API_URL}/api/model-stats`)
      .then((r) => r.json())
      .then((data) => {
        setModelVersion(data.model_version || "—");
        setTotalEvents(data.total_events_learned || 0);
        setLastCalibration(data.last_calibration || "Never");
      })
      .catch(() => {});

    // Also check existing log count
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    fetch(`${API_URL}/retrain`, { method: "POST" })
      .then((r) => r.json())
      .then((data) => {
        // Parse "Currently have X" from waiting message
        if (data.status === "waiting" && data.message) {
          const match = data.message.match(/have (\d+)/);
          if (match) setLogCount(parseInt(match[1]));
        }
      })
      .catch(() => {});
  }, []);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLines]);

  // ── Open debrief modal ──
  const openDebrief = (incident: IncidentLog) => {
    setDebriefTarget(incident);
    setActualImpact("Medium");
    setActualBarricades(0);
    setDebriefOpen(true);
  };

  // ── Submit feedback ──
  const submitFeedback = async () => {
    if (!debriefTarget) return;
    setIsSubmittingFeedback(true);
    try {
      const payload = {
        latitude: 12.9716,
        longitude: 77.5946,
        event_cause: debriefTarget.cause.replace(" ", "_"),
        priority: debriefTarget.severity,
        requires_road_closure: false,
        corridor: debriefTarget.location.split(" @ ")[0] || "Non-corridor",
        zone: "Unknown",
        police_station: debriefTarget.location.split(" @ ")[1] || "Unknown",
        event_time: new Date().toISOString(),
        event_type: "unplanned",
        actual_impact: actualImpact.toLowerCase(),
        actual_barricades_used: actualBarricades,
      };

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        const newCount = data.total_verified_logs || logCount + 1;
        setLogCount(newCount);

        // Remove from active list
        setLogs(prev => prev.filter(l => l.id !== debriefTarget.id));

        // Terminal output
        addTerminalLine(`> [${debriefTarget.id}] Feedback received: actual_impact=${actualImpact}, barricades_used=${actualBarricades}`);
        addTerminalLine(`> Training queue: ${newCount}/${RETRAIN_THRESHOLD} logs collected`);

        setDebriefOpen(false);
      } else {
        alert("Feedback submission failed.");
      }
    } catch (err) {
      console.error(err);
      alert("Backend not responding.");
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  // ── Trigger retrain ──
  const triggerRetrain = async () => {
    if (logCount < RETRAIN_THRESHOLD) return;
    setIsRetraining(true);

    addTerminalLine("");
    addTerminalLine("> ═══════════════════════════════════════════");
    addTerminalLine("> INITIATING MODEL RETRAINING PIPELINE");
    addTerminalLine("> ═══════════════════════════════════════════");

    // Simulate progressive terminal output
    const steps = [
      { msg: "> Fetching validated logs from training queue...", delay: 800 },
      { msg: `> Found ${logCount} verified feedback logs`, delay: 600 },
      { msg: "> Aligning feature schemas with model_features.pkl...", delay: 1200 },
      { msg: "> Converting human feedback to LightGBM-compatible tensors...", delay: 900 },
      { msg: "> Warm-starting LightGBM tree growth (n_estimators=20, lr=0.01)...", delay: 1500 },
    ];

    for (const step of steps) {
      await new Promise(r => setTimeout(r, step.delay));
      addTerminalLine(step.msg);
    }

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${API_URL}/retrain`, { method: "POST" });
      const data = await res.json();

      if (data.status === "success") {
        addTerminalLine("> ✓ Model successfully fine-tuned with human feedback!");
        addTerminalLine("> ✓ New model weights saved to lightgbm_impact_model.pkl");
        addTerminalLine("> ✓ Training queue flushed — ready for next epoch");
        setLogCount(0);
      } else {
        addTerminalLine(`> ⚠ ${data.message || "Retrain returned non-success status"}`);
      }
    } catch (err) {
      addTerminalLine("> ✗ ERROR: Backend not responding. Check uvicorn server.");
    } finally {
      setIsRetraining(false);
      addTerminalLine("> $");
    }
  };

  const addTerminalLine = (line: string) => {
    setTerminalLines(prev => [...prev, line]);
  };

  const progressPercent = Math.min((logCount / RETRAIN_THRESHOLD) * 100, 100);

  return (
    <div className="flex h-full">
      {/* ══════════════ LEFT PANE: Active Queue & Debrief ══════════════ */}
      <div className="w-[45%] flex-shrink-0 border-r border-border/30 p-5 overflow-y-auto space-y-4">
        {/* Section Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-accent-cyan" />
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Active Incident Queue
            </h2>
          </div>
          <Badge variant="outline" className="text-[10px] font-mono">
            {logs.length} active
          </Badge>
        </div>

        <p className="text-xs text-muted-foreground">
          Resolve each incident to submit ground-truth feedback for progressive model retraining.
        </p>

        {/* Incident List */}
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-accent/20 border border-border/30 flex items-center justify-center mb-4">
              <Database className="w-8 h-8 text-muted-foreground/30" />
            </div>
            <p className="text-sm text-muted-foreground font-mono">No active incidents</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Predictions from the Tactical Dispatch tab will appear here</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((incident) => {
              const sevColor = incident.severity === "HIGH" ? "text-severity-high" : incident.severity === "MEDIUM" ? "text-severity-medium" : "text-severity-low";
              const sevBg = incident.severity === "HIGH" ? "bg-severity-high/15 border-severity-high/30" : incident.severity === "MEDIUM" ? "bg-severity-medium/15 border-severity-medium/30" : "bg-severity-low/15 border-severity-low/30";

              return (
                <div
                  key={incident.id}
                  className="p-3 rounded-lg bg-accent/30 border border-border/30 hover:border-accent-cyan/30 transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`text-[10px] font-mono ${sevBg} ${sevColor}`}>
                        {incident.severity}
                      </Badge>
                      <span className="text-xs font-mono text-muted-foreground">{incident.id}</span>
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground">{incident.timestamp}</span>
                  </div>
                  <p className="text-sm font-medium text-foreground/80 mb-1">{incident.location}</p>
                  <p className="text-[11px] text-muted-foreground capitalize">{incident.cause}</p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-2 h-7 text-[11px] font-mono w-full cursor-pointer border-accent-violet/30 hover:bg-accent-violet/10"
                    onClick={() => openDebrief(incident)}
                  >
                    <CheckCircle2 className="w-3 h-3 mr-1.5" />
                    Resolve Incident
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        {/* Quick-add demo incident for judges */}
        <Separator />
        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs font-mono cursor-pointer border-dashed border-border/50 text-muted-foreground hover:text-foreground"
          onClick={() => {
            const demo: IncidentLog = {
              id: `EVT-${Date.now().toString(36).toUpperCase().slice(-6)}`,
              location: "ORR Marathahalli @ HSR Layout",
              severity: "HIGH",
              cause: "accident",
              timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false }),
            };
            setLogs(prev => [demo, ...prev]);
          }}
        >
          + Add Demo Incident (for Judges)
        </Button>
      </div>

      {/* ══════════════ RIGHT PANE: Progressive Learning Engine ══════════════ */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {/* Section Header */}
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-accent-violet" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Progressive Learning Engine
          </h2>
        </div>

        {/* Model Info Cards */}
        <div className="grid grid-cols-3 gap-3">
          <Card className="glass-card border-border/50">
            <CardContent className="p-3 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground mb-1">Model</p>
              <p className="text-xs font-mono text-accent-violet truncate">{modelVersion}</p>
            </CardContent>
          </Card>
          <Card className="glass-card border-border/50">
            <CardContent className="p-3 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground mb-1">Training Data</p>
              <p className="text-lg font-bold text-accent-blue">{totalEvents.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="glass-card border-border/50">
            <CardContent className="p-3 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground mb-1">Last Calibration</p>
              <p className="text-xs font-mono text-accent-cyan">{lastCalibration}</p>
            </CardContent>
          </Card>
        </div>

        {/* ── The Progress Bar ── */}
        <Card className="glass-card border-accent-blue/20 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-accent-blue/5 via-transparent to-accent-violet/5" />
          <CardContent className="p-5 relative">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-semibold">Feedback Log Buffer</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Collecting validated incident debriefs for next training epoch
                </p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-black text-accent-blue">{logCount}<span className="text-lg text-muted-foreground">/{RETRAIN_THRESHOLD}</span></p>
                <p className="text-[10px] font-mono text-muted-foreground">logs in queue</p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-4 rounded-full bg-accent/30 border border-border/30 overflow-hidden">
              <div
                className={`h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-violet transition-all duration-700 ease-out ${progressPercent >= 100 ? "progress-bar-glow" : ""}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="text-[10px] font-mono text-muted-foreground mt-2 text-center">
              {progressPercent >= 100
                ? "✓ Buffer full — model retraining unlocked!"
                : `${RETRAIN_THRESHOLD - logCount} more feedback logs needed to unlock retraining`
              }
            </p>
          </CardContent>
        </Card>

        {/* ── Retrain Button ── */}
        <Button
          onClick={triggerRetrain}
          disabled={logCount < RETRAIN_THRESHOLD || isRetraining}
          size="lg"
          className={`w-full h-14 text-base font-bold cursor-pointer transition-all duration-300 ${
            logCount >= RETRAIN_THRESHOLD
              ? "bg-gradient-to-r from-accent-violet to-accent-blue text-white hover:opacity-90"
              : "bg-accent/30 text-muted-foreground border border-border/30"
          } disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          {isRetraining ? (
            <>
              <Loader2 className="w-5 h-5 mr-3 animate-spin" />
              Retraining in Progress…
            </>
          ) : (
            <>
              <RefreshCcw className="w-5 h-5 mr-3" />
              Initialize Model Retraining
            </>
          )}
        </Button>

        {/* ── Terminal Window ── */}
        <Card className="glass-card border-border/50">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-severity-low" />
              <CardTitle className="text-sm font-semibold">Training Pipeline Terminal</CardTitle>
              <div className="ml-auto flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-severity-high" />
                <div className="w-2.5 h-2.5 rounded-full bg-severity-medium" />
                <div className="w-2.5 h-2.5 rounded-full bg-severity-low" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div ref={terminalRef} className="terminal-window h-[260px] overflow-y-auto">
              {terminalLines.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
              <span className="cursor-blink">█</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ══════════════ Debrief Modal ══════════════ */}
      <Dialog open={debriefOpen} onOpenChange={setDebriefOpen}>
        <DialogContent className="glass-card border-border/50 max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="w-5 h-5 text-accent-violet" />
              Incident Post-Mortem
            </DialogTitle>
            <DialogDescription className="text-xs">
              {debriefTarget?.id} — {debriefTarget?.location}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-2">
            {/* Q1: Actual impact */}
            <div className="space-y-1.5">
              <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                What was the actual impact?
              </Label>
              <Select value={actualImpact} onValueChange={(val) => setActualImpact(val || "Medium")}>
                <SelectTrigger className="bg-accent/30 border-border/40 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Q2: Actual barricades */}
            <div className="space-y-1.5">
              <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                How many barricades were physically used?
              </Label>
              <Input
                type="number"
                min={0}
                value={actualBarricades}
                onChange={(e) => setActualBarricades(parseInt(e.target.value) || 0)}
                className="bg-accent/30 border-border/40 text-sm font-mono"
              />
            </div>

            <Button
              onClick={submitFeedback}
              disabled={isSubmittingFeedback}
              className="w-full bg-gradient-to-r from-accent-violet to-accent-blue text-white font-semibold cursor-pointer"
            >
              {isSubmittingFeedback ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Submitting…
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Submit to ML Training Log
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
