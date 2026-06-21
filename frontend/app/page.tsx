"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Clock,
  Cpu,
  Radio,
  Signal,
} from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LiveOperationsTab } from "@/components/tabs/live-operations";
import { ModelLearningTab } from "@/components/tabs/model-learning";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("live-operations");
  const [currentTime, setCurrentTime] = useState("--:--");

  useEffect(() => {
    const updateTime = () =>
      setCurrentTime(
        new Date().toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })
      );
    updateTime();
    const interval = setInterval(updateTime, 1000);
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
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-severity-low border-2 border-background animate-pulse-glow" />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight">
                <span className="gradient-text">Flipkart AI</span>{" "}
                <span className="text-foreground/80">Traffic Command Center</span>
              </h1>
              <p className="text-[11px] text-muted-foreground font-mono tracking-wide">
                HYDERABAD METRO · REAL-TIME OPS
              </p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Signal className="w-3.5 h-3.5 text-severity-low" />
              <span className="font-mono">SYSTEM ONLINE</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-mono">{currentTime}</span>
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
              <Radio className="w-4 h-4 mr-2" />
              Live Operations
              <span className="ml-2 px-1.5 py-0.5 text-[10px] font-mono rounded-sm bg-severity-high/20 text-severity-high">
                8
              </span>
            </TabsTrigger>
            <TabsTrigger
              value="model-learning"
              className="relative rounded-none border-b-2 border-transparent data-[state=active]:border-accent-violet data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none text-muted-foreground bg-transparent px-4 py-2.5 text-sm font-medium transition-all duration-200 hover:text-foreground/80 cursor-pointer"
            >
              <Brain className="w-4 h-4 mr-2" />
              Model Learning & Analytics
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-y-auto">
          <TabsContent
            value="live-operations"
            className="mt-0 h-full"
          >
            <LiveOperationsTab />
          </TabsContent>
          <TabsContent
            value="model-learning"
            className="mt-0 h-full"
          >
            <ModelLearningTab />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
