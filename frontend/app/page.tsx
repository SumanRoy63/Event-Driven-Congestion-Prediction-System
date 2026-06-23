"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Clock,
  Cpu,
  Radio,
  Signal,
  Crosshair,
  BarChart3,
} from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LiveOperationsTab } from "@/components/tabs/live-operations";
import { ModelLearningTab } from "@/components/tabs/model-learning";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("live-operations");
  const [currentTime, setCurrentTime] = useState("--:--:--");
  const [engineOnline, setEngineOnline] = useState(false);
  const [sharedIncidents, setSharedIncidents] = useState<any[]>([]);

  useEffect(() => {
    // Live clock with seconds
    const updateTime = () =>
      setCurrentTime(
        new Date().toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    updateTime();
    const interval = setInterval(updateTime, 1000);

    // Check backend health
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    fetch(`${API_URL}/api/model-stats`)
      .then((r) => { if (r.ok) setEngineOnline(true); })
      .catch(() => setEngineOnline(false));

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden grid-pattern">
      {/* ══════════════ Top Navigation Bar ══════════════ */}
      <header className="flex-shrink-0 border-b border-border/50 glass-card">
        <div className="flex items-center justify-between px-6 py-3">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-blue to-accent-violet flex items-center justify-center">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <div className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-background ${engineOnline ? "bg-severity-low animate-pulse-glow" : "bg-severity-high"}`} />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight">
                <span className="gradient-text">Flipkart AI</span>{" "}
                <span className="text-foreground/80">Traffic Command Center</span>
              </h1>
              <p className="text-[11px] text-muted-foreground font-mono tracking-wide">
                BENGALURU METRO · REAL-TIME OPS
              </p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <div className={`w-2 h-2 rounded-full ${engineOnline ? "bg-severity-low" : "bg-severity-high animate-pulse"}`} />
              <span className="font-mono">LightGBM: {engineOnline ? "Online" : "Offline"}</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <div className={`w-2 h-2 rounded-full ${engineOnline ? "bg-severity-low" : "bg-severity-high"}`} />
              <span className="font-mono">LLM: {engineOnline ? "Connected" : "—"}</span>
            </div>
            <div className="h-4 w-px bg-border/50" />
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-mono tabular-nums">{currentTime}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-severity-low animate-pulse-glow" />
              <span className="text-xs font-mono text-severity-low">LIVE</span>
            </div>
          </div>
        </div>
      </header>

      {/* ══════════════ Main Content with Tabs ══════════════ */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* Tab Selector Bar */}
        <div className="flex-shrink-0 border-b border-border/30 px-6">
          <TabsList className="bg-transparent h-11 gap-1 p-0">
            <TabsTrigger
              value="live-operations"
              className="relative rounded-none border-b-2 border-transparent data-[state=active]:border-accent-blue data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none text-muted-foreground bg-transparent px-4 py-2.5 text-sm font-medium transition-all duration-200 hover:text-foreground/80 cursor-pointer"
            >
              <Crosshair className="w-4 h-4 mr-2" />
              Tactical Dispatch
              {sharedIncidents.length > 0 && (
                <span className="ml-2 px-1.5 py-0.5 text-[10px] font-mono rounded-sm bg-severity-high/20 text-severity-high">
                  {sharedIncidents.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger
              value="model-learning"
              className="relative rounded-none border-b-2 border-transparent data-[state=active]:border-accent-violet data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none text-muted-foreground bg-transparent px-4 py-2.5 text-sm font-medium transition-all duration-200 hover:text-foreground/80 cursor-pointer"
            >
              <Brain className="w-4 h-4 mr-2" />
              MLOps & Retraining Hub
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-y-auto">
          <TabsContent
            value="live-operations"
            className="mt-0 h-full"
          >
            <LiveOperationsTab sharedIncidents={sharedIncidents} setSharedIncidents={setSharedIncidents} />
          </TabsContent>
          <TabsContent
            value="model-learning"
            className="mt-0 h-full"
          >
            <ModelLearningTab sharedIncidents={sharedIncidents} setSharedIncidents={setSharedIncidents} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
