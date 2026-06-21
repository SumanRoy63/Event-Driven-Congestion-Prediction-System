"use client";

import React, { useState } from "react";
import {
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  Gauge,
  RefreshCcw,
  Target,
  TrendingUp,
  Zap,
  Loader2,
  BarChart3,
  Clock,
  Sparkles,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

import {
  modelKPIs,
  severityComparisonData,
  recentCalibrations,
} from "@/lib/mock-data";

const chartConfig: ChartConfig = {
  predicted: {
    label: "Predicted Severity",
    color: "oklch(0.623 0.214 259.13)",
  },
  actual: {
    label: "Actual Severity",
    color: "oklch(0.541 0.281 293.54)",
  },
};

export function ModelLearningTab() {
  const [isCalibrating, setIsCalibrating] = useState(false);

  const handleCalibration = () => {
    setIsCalibrating(true);
    setTimeout(() => setIsCalibrating(false), 3000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* ══════════════ Model KPI Header Cards ══════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Model Accuracy */}
        <Card className="glass-card border-accent-violet/20 relative overflow-hidden group hover:border-accent-violet/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-violet/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-accent-violet/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Model Accuracy
                </p>
                <div className="flex items-baseline gap-1">
                  <p className="text-4xl font-bold tracking-tight text-accent-violet">
                    {modelKPIs.accuracy}
                  </p>
                  <span className="text-lg text-accent-violet/70">%</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-severity-low" />
                  <span className="text-severity-low">+0.8%</span> this week
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-accent-violet/10 flex items-center justify-center">
                <Target className="w-5 h-5 text-accent-violet" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Resource Efficiency */}
        <Card className="glass-card border-accent-cyan/20 relative overflow-hidden group hover:border-accent-cyan/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-cyan/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-accent-cyan/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Resource Efficiency
                </p>
                <div className="flex items-baseline gap-1">
                  <p className="text-4xl font-bold tracking-tight text-accent-cyan">
                    {modelKPIs.resourceEfficiency}
                  </p>
                  <span className="text-lg text-accent-cyan/70">%</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Gauge className="w-3 h-3 text-accent-cyan" />
                  Officer allocation score
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
                <Gauge className="w-5 h-5 text-accent-cyan" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Events Learned */}
        <Card className="glass-card border-accent-blue/20 relative overflow-hidden group hover:border-accent-blue/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-blue/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-accent-blue/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Events Learned
                </p>
                <p className="text-4xl font-bold tracking-tight text-accent-blue">
                  {modelKPIs.totalEventsLearned.toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Database className="w-3 h-3 text-accent-blue" />
                  Training corpus size
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-accent-blue/10 flex items-center justify-center">
                <Database className="w-5 h-5 text-accent-blue" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* F1 Score */}
        <Card className="glass-card border-severity-low/20 relative overflow-hidden group hover:border-severity-low/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-severity-low/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-severity-low/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  F1 Score
                </p>
                <p className="text-4xl font-bold tracking-tight text-severity-low">
                  {modelKPIs.f1Score}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-severity-low" />
                  Weighted macro average
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-severity-low/10 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-severity-low" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ══════════════ Chart + Calibration Panel ══════════════ */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Severity Comparison Chart — spans 2 columns */}
        <Card className="xl:col-span-2 glass-card border-border/50">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-accent-violet" />
                  Predicted vs Actual Severity
                </CardTitle>
                <CardDescription className="text-xs mt-1">
                  Weekly comparison across 12-week rolling window · Model{" "}
                  <span className="font-mono text-accent-violet">
                    {modelKPIs.modelVersion}
                  </span>
                </CardDescription>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-accent-blue" />
                  <span className="text-[11px] text-muted-foreground">
                    Predicted
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-accent-violet" />
                  <span className="text-[11px] text-muted-foreground">
                    Actual
                  </span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <ChartContainer config={chartConfig} className="h-[320px] w-full">
              <AreaChart
                data={severityComparisonData}
                margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient
                    id="gradPredicted"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor="oklch(0.623 0.214 259.13)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="oklch(0.623 0.214 259.13)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                  <linearGradient
                    id="gradActual"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor="oklch(0.541 0.281 293.54)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="oklch(0.541 0.281 293.54)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="oklch(0.25 0.012 260)"
                  vertical={false}
                />
                <XAxis
                  dataKey="week"
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fontSize: 11,
                    fill: "oklch(0.6 0.02 260)",
                    fontFamily: "var(--font-geist-mono)",
                  }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fontSize: 11,
                    fill: "oklch(0.6 0.02 260)",
                    fontFamily: "var(--font-geist-mono)",
                  }}
                />
                <ChartTooltip
                  content={<ChartTooltipContent indicator="dot" />}
                />
                <Area
                  type="monotone"
                  dataKey="predicted"
                  stroke="oklch(0.623 0.214 259.13)"
                  strokeWidth={2}
                  fill="url(#gradPredicted)"
                  dot={{
                    r: 3,
                    fill: "oklch(0.623 0.214 259.13)",
                    stroke: "oklch(0.098 0.005 260)",
                    strokeWidth: 2,
                  }}
                  activeDot={{
                    r: 5,
                    fill: "oklch(0.623 0.214 259.13)",
                    stroke: "oklch(0.098 0.005 260)",
                    strokeWidth: 2,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="oklch(0.541 0.281 293.54)"
                  strokeWidth={2}
                  fill="url(#gradActual)"
                  dot={{
                    r: 3,
                    fill: "oklch(0.541 0.281 293.54)",
                    stroke: "oklch(0.098 0.005 260)",
                    strokeWidth: 2,
                  }}
                  activeDot={{
                    r: 5,
                    fill: "oklch(0.541 0.281 293.54)",
                    stroke: "oklch(0.098 0.005 260)",
                    strokeWidth: 2,
                  }}
                />
              </AreaChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* ══════════════ Calibration Panel ══════════════ */}
        <div className="space-y-6">
          {/* Run Calibration Card */}
          <Card className="glass-card border-accent-violet/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-accent-violet/5 via-transparent to-accent-blue/5" />
            <CardContent className="p-5 relative">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="w-5 h-5 text-accent-violet" />
                <h3 className="font-semibold text-sm">
                  Incremental Calibration
                </h3>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed mb-4">
                Update model weights using feedback from recently resolved
                events. This process fine-tunes the severity prediction and
                closure probability models without requiring a full retrain.
              </p>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-4">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Last: {modelKPIs.lastCalibration}
                </div>
                <span className="text-border">·</span>
                <div className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  {modelKPIs.modelVersion}
                </div>
              </div>
              <Button
                onClick={handleCalibration}
                disabled={isCalibrating}
                className="w-full bg-gradient-to-r from-accent-violet to-accent-blue hover:opacity-90 text-white font-medium transition-all duration-300 cursor-pointer disabled:opacity-50"
                size="lg"
              >
                {isCalibrating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Calibrating Model...
                  </>
                ) : (
                  <>
                    <RefreshCcw className="w-4 h-4 mr-2" />
                    Run Incremental Calibration
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Recent Calibration History */}
          <Card className="glass-card border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                Recent Calibrations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {recentCalibrations.map((cal) => (
                <div
                  key={cal.id}
                  className="flex items-center justify-between p-2.5 rounded-md bg-accent/20 border border-border/20 hover:border-border/40 transition-colors duration-150"
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-6 h-6 rounded flex items-center justify-center ${
                        cal.status === "Success"
                          ? "bg-severity-low/15"
                          : "bg-severity-medium/15"
                      }`}
                    >
                      {cal.status === "Success" ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-severity-low" />
                      ) : (
                        <Zap className="w-3.5 h-3.5 text-severity-medium" />
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-mono text-foreground/80">
                        {cal.id}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {cal.eventsProcessed} events · {cal.timestamp}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-[10px] font-mono ${
                      cal.accuracyDelta.startsWith("+")
                        ? "bg-severity-low/10 text-severity-low border-severity-low/30"
                        : "bg-severity-medium/10 text-severity-medium border-severity-medium/30"
                    }`}
                  >
                    {cal.accuracyDelta}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
