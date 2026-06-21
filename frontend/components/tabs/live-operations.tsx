"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Eye,
  MapPin,
  Route,
  Shield,
  Siren,
  Users,
  Zap,
  Activity,
  TrendingUp,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  liveKPIs,
  trafficEvents,
  diversionStrategies,
  type SeverityLevel,
  type TrafficEvent,
} from "@/lib/mock-data";

// ── Severity badge color mapping ──
function getSeverityClasses(severity: SeverityLevel) {
  switch (severity) {
    case "High":
      return "bg-severity-high/15 text-severity-high border-severity-high/30 hover:bg-severity-high/25";
    case "Medium":
      return "bg-severity-medium/15 text-severity-medium border-severity-medium/30 hover:bg-severity-medium/25";
    case "Low":
      return "bg-severity-low/15 text-severity-low border-severity-low/30 hover:bg-severity-low/25";
  }
}

function getStatusClasses(status: string) {
  switch (status) {
    case "Active":
      return "bg-accent-blue/15 text-accent-blue border-accent-blue/30";
    case "Escalated":
      return "bg-severity-high/15 text-severity-high border-severity-high/30";
    case "Monitoring":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function getDiversionStatusClasses(status: string) {
  switch (status) {
    case "Active":
      return "bg-severity-low/15 text-severity-low border-severity-low/30";
    case "Pending":
      return "bg-severity-medium/15 text-severity-medium border-severity-medium/30";
    case "Completed":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

export function LiveOperationsTab() {
  const [dispatchDialog, setDispatchDialog] = useState<TrafficEvent | null>(null);

  return (
    <div className="p-6 space-y-6">
      {/* ══════════════ KPI Header Cards ══════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Events */}
        <Card className="glass-card border-severity-high/20 relative overflow-hidden group hover:border-severity-high/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-severity-high/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-severity-high/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Active Events
                </p>
                <p className="text-4xl font-bold tracking-tight text-severity-high">
                  {liveKPIs.activeEvents}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-severity-high" />
                  +2 in last hour
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-severity-high/10 flex items-center justify-center">
                <Siren className="w-5 h-5 text-severity-high" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Officers Deployed */}
        <Card className="glass-card border-accent-blue/20 relative overflow-hidden group hover:border-accent-blue/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-blue/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-accent-blue/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Officers Deployed
                </p>
                <p className="text-4xl font-bold tracking-tight text-accent-blue">
                  {liveKPIs.officersDeployed}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Users className="w-3 h-3 text-accent-blue" />
                  86% utilization
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-accent-blue/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-accent-blue" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Predicted Closures */}
        <Card className="glass-card border-severity-medium/20 relative overflow-hidden group hover:border-severity-medium/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-severity-medium/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-severity-medium/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Predicted Closures
                </p>
                <p className="text-4xl font-bold tracking-tight text-severity-medium">
                  {liveKPIs.predictedClosures}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-severity-medium" />
                  Next 2 hours
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-severity-medium/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-severity-medium" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Avg Response Time */}
        <Card className="glass-card border-severity-low/20 relative overflow-hidden group hover:border-severity-low/40 transition-colors duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-severity-low/5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:bg-severity-low/10 transition-all duration-500" />
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                  Avg Response Time
                </p>
                <p className="text-4xl font-bold tracking-tight text-severity-low">
                  {liveKPIs.avgResponseTime}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Activity className="w-3 h-3 text-severity-low" />
                  -12% vs yesterday
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-severity-low/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-severity-low" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ══════════════ Table + Diversion Side-by-Side ══════════════ */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Live Incidents Table — spans 2 columns */}
        <Card className="xl:col-span-2 glass-card border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-severity-high animate-pulse-glow" />
                <CardTitle className="text-base font-semibold">
                  Live Incident Feed
                </CardTitle>
                <Badge
                  variant="outline"
                  className="text-[10px] font-mono bg-severity-high/10 text-severity-high border-severity-high/30"
                >
                  {trafficEvents.length} ACTIVE
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                <Eye className="w-3.5 h-3.5 mr-1" />
                View All
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30 hover:bg-transparent">
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9 pl-6">
                      Event ID
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9">
                      Location / Zone
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9">
                      Event Type
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9">
                      Severity
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9 text-center">
                      Closure Prob.
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9">
                      Status
                    </TableHead>
                    <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground h-9 text-right pr-6">
                      Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trafficEvents.map((event) => (
                    <TableRow
                      key={event.id}
                      className="border-border/20 hover:bg-accent/30 transition-colors duration-150 group"
                    >
                      <TableCell className="pl-6 py-3">
                        <span className="font-mono text-xs text-accent-cyan font-medium">
                          {event.id}
                        </span>
                      </TableCell>
                      <TableCell className="py-3">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <MapPin className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                            <span className="text-sm font-medium truncate max-w-[180px]">
                              {event.location}
                            </span>
                          </div>
                          <span className="text-[11px] text-muted-foreground font-mono ml-[18px]">
                            {event.zone}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="py-3">
                        <span className="text-sm">{event.eventType}</span>
                      </TableCell>
                      <TableCell className="py-3">
                        <Badge
                          variant="outline"
                          className={`text-[11px] font-semibold ${getSeverityClasses(event.severity)}`}
                        >
                          {event.severity === "High" && (
                            <AlertTriangle className="w-3 h-3 mr-1" />
                          )}
                          {event.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="py-3 text-center">
                        <div className="flex flex-col items-center">
                          <span
                            className={`text-sm font-mono font-bold ${
                              event.closureProbability >= 0.7
                                ? "text-severity-high"
                                : event.closureProbability >= 0.4
                                ? "text-severity-medium"
                                : "text-severity-low"
                            }`}
                          >
                            {(event.closureProbability * 100).toFixed(0)}%
                          </span>
                          {/* Mini progress bar */}
                          <div className="w-12 h-1 bg-muted rounded-full mt-1 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                event.closureProbability >= 0.7
                                  ? "bg-severity-high"
                                  : event.closureProbability >= 0.4
                                  ? "bg-severity-medium"
                                  : "bg-severity-low"
                              }`}
                              style={{
                                width: `${event.closureProbability * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="py-3">
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-mono ${getStatusClasses(event.status)}`}
                        >
                          {event.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="py-3 pr-6">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            className="h-7 text-xs bg-accent-blue hover:bg-accent-blue/80 text-white cursor-pointer"
                            onClick={() => setDispatchDialog(event)}
                          >
                            <Users className="w-3 h-3 mr-1" />
                            Dispatch
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs border-severity-low/30 text-severity-low hover:bg-severity-low/10 hover:text-severity-low cursor-pointer"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Resolve
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* ══════════════ Diversion Strategies Panel ══════════════ */}
        <Card className="glass-card border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Route className="w-4 h-4 text-accent-cyan" />
              <CardTitle className="text-base font-semibold">
                Active Diversion Strategies
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              AI-optimized routing instructions for congested zones
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {diversionStrategies.map((strategy) => (
              <div
                key={strategy.id}
                className="p-3 rounded-lg bg-accent/30 border border-border/30 hover:border-accent-cyan/30 transition-all duration-200 group"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`text-[10px] font-mono ${getDiversionStatusClasses(strategy.status)}`}
                    >
                      {strategy.status}
                    </Badge>
                    <span className="text-xs font-mono text-muted-foreground">
                      {strategy.id}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-severity-medium">
                    {strategy.estimatedDelay}
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-5 h-5 rounded bg-accent-cyan/10 flex items-center justify-center mt-0.5">
                    <ChevronRight className="w-3 h-3 text-accent-cyan" />
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-0.5">
                      {strategy.sourceZone}{" "}
                      <span className="text-muted-foreground font-normal">→</span>{" "}
                      <span className="text-accent-cyan">
                        {strategy.instruction}
                      </span>
                    </p>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      {strategy.alternateRoute}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ══════════════ Dispatch Dialog (rendered once) ══════════════ */}
      <Dialog
        open={dispatchDialog !== null}
        onOpenChange={(open) => !open && setDispatchDialog(null)}
      >
        <DialogContent className="glass-card border-border/50">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-accent-blue" />
              Dispatch Officers
            </DialogTitle>
            <DialogDescription>
              Deploy additional officers to{" "}
              <span className="text-foreground font-medium">
                {dispatchDialog?.location}
              </span>{" "}
              ({dispatchDialog?.zone}). Currently{" "}
              <span className="text-accent-blue font-mono">
                {dispatchDialog?.officersAssigned}
              </span>{" "}
              officers assigned.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Event Type</span>
              <span className="font-medium">{dispatchDialog?.eventType}</span>
            </div>
            <Separator className="bg-border/30" />
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Severity</span>
              {dispatchDialog && (
                <Badge
                  variant="outline"
                  className={`text-[11px] ${getSeverityClasses(dispatchDialog.severity)}`}
                >
                  {dispatchDialog.severity}
                </Badge>
              )}
            </div>
            <Separator className="bg-border/30" />
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Closure Probability</span>
              <span className="font-mono font-bold text-severity-high">
                {dispatchDialog
                  ? `${(dispatchDialog.closureProbability * 100).toFixed(0)}%`
                  : "—"}
              </span>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setDispatchDialog(null)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              className="bg-accent-blue hover:bg-accent-blue/80 text-white cursor-pointer"
              onClick={() => setDispatchDialog(null)}
            >
              <Users className="w-4 h-4 mr-1" />
              Confirm Dispatch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
