// ═══════════════════════════════════════════
// Mock Data for Flipkart AI Traffic Command Center
// ═══════════════════════════════════════════

export type SeverityLevel = "High" | "Medium" | "Low";

export interface TrafficEvent {
  id: string;
  location: string;
  zone: string;
  eventType: string;
  severity: SeverityLevel;
  closureProbability: number;
  reportedAt: string;
  status: "Active" | "Monitoring" | "Escalated";
  officersAssigned: number;
}

export interface DiversionStrategy {
  id: string;
  sourceZone: string;
  instruction: string;
  alternateRoute: string;
  status: "Active" | "Pending" | "Completed";
  estimatedDelay: string;
}

export interface SeverityComparisonData {
  week: string;
  predicted: number;
  actual: number;
}

// ── Live Operations Data ──────────────────

export const liveKPIs = {
  activeEvents: 8,
  officersDeployed: 42,
  predictedClosures: 3,
  avgResponseTime: "4.2 min",
};

export const trafficEvents: TrafficEvent[] = [
  {
    id: "EVT-2026-0847",
    location: "Jubilee Hills Checkpost",
    zone: "Zone A",
    eventType: "Metro Construction",
    severity: "High",
    closureProbability: 0.92,
    reportedAt: "14:23",
    status: "Escalated",
    officersAssigned: 6,
  },
  {
    id: "EVT-2026-0848",
    location: "Gachibowli Junction",
    zone: "Zone B",
    eventType: "VIP Movement",
    severity: "High",
    closureProbability: 0.87,
    reportedAt: "14:45",
    status: "Active",
    officersAssigned: 8,
  },
  {
    id: "EVT-2026-0849",
    location: "HITEC City Signal",
    zone: "Zone B",
    eventType: "Signal Malfunction",
    severity: "Medium",
    closureProbability: 0.54,
    reportedAt: "15:02",
    status: "Active",
    officersAssigned: 3,
  },
  {
    id: "EVT-2026-0850",
    location: "Kukatpally Y-Junction",
    zone: "Zone C",
    eventType: "Accident Report",
    severity: "High",
    closureProbability: 0.78,
    reportedAt: "15:10",
    status: "Active",
    officersAssigned: 5,
  },
  {
    id: "EVT-2026-0851",
    location: "Madhapur ORR Entry",
    zone: "Zone B",
    eventType: "Waterlogging",
    severity: "Medium",
    closureProbability: 0.45,
    reportedAt: "15:18",
    status: "Monitoring",
    officersAssigned: 2,
  },
  {
    id: "EVT-2026-0852",
    location: "Begumpet Railway Crossing",
    zone: "Zone A",
    eventType: "Train Crossing",
    severity: "Low",
    closureProbability: 0.23,
    reportedAt: "15:30",
    status: "Monitoring",
    officersAssigned: 1,
  },
  {
    id: "EVT-2026-0853",
    location: "Secunderabad Parade Grounds",
    zone: "Zone D",
    eventType: "Public Rally",
    severity: "Medium",
    closureProbability: 0.61,
    reportedAt: "15:35",
    status: "Active",
    officersAssigned: 7,
  },
  {
    id: "EVT-2026-0854",
    location: "LB Nagar Crossroads",
    zone: "Zone E",
    eventType: "Road Maintenance",
    severity: "Low",
    closureProbability: 0.18,
    reportedAt: "15:42",
    status: "Monitoring",
    officersAssigned: 2,
  },
];

export const diversionStrategies: DiversionStrategy[] = [
  {
    id: "DIV-001",
    sourceZone: "Zone A Blockade",
    instruction: "Rerouting via Ring Road",
    alternateRoute: "Jubilee Hills → Banjara Hills → Panjagutta Ring Road",
    status: "Active",
    estimatedDelay: "+8 min",
  },
  {
    id: "DIV-002",
    sourceZone: "Zone B Congestion",
    instruction: "Split traffic to Service Road",
    alternateRoute: "Gachibowli → Nanakramguda Service Rd → Raidurg",
    status: "Active",
    estimatedDelay: "+5 min",
  },
  {
    id: "DIV-003",
    sourceZone: "Zone C Accident",
    instruction: "Bypass via KPHB Colony",
    alternateRoute: "Kukatpally → KPHB Phase-III → Miyapur",
    status: "Pending",
    estimatedDelay: "+12 min",
  },
  {
    id: "DIV-004",
    sourceZone: "Zone D Rally Perimeter",
    instruction: "Closure + alternate corridor",
    alternateRoute: "Secunderabad → Tarnaka → Uppal bypass",
    status: "Active",
    estimatedDelay: "+15 min",
  },
];

// ── Model Learning Data ──────────────────

export const modelKPIs = {
  accuracy: 91.2,
  resourceEfficiency: 88,
  totalEventsLearned: 1240,
  lastCalibration: "2 hours ago",
  modelVersion: "v3.4.1",
  f1Score: 0.89,
};

export const severityComparisonData: SeverityComparisonData[] = [
  { week: "W1", predicted: 12, actual: 14 },
  { week: "W2", predicted: 19, actual: 17 },
  { week: "W3", predicted: 15, actual: 16 },
  { week: "W4", predicted: 22, actual: 20 },
  { week: "W5", predicted: 28, actual: 25 },
  { week: "W6", predicted: 18, actual: 19 },
  { week: "W7", predicted: 24, actual: 22 },
  { week: "W8", predicted: 31, actual: 29 },
  { week: "W9", predicted: 20, actual: 21 },
  { week: "W10", predicted: 26, actual: 24 },
  { week: "W11", predicted: 16, actual: 18 },
  { week: "W12", predicted: 23, actual: 22 },
];

export const recentCalibrations = [
  {
    id: "CAL-041",
    timestamp: "2026-06-21 13:00",
    eventsProcessed: 34,
    accuracyDelta: "+0.3%",
    status: "Success" as const,
  },
  {
    id: "CAL-040",
    timestamp: "2026-06-21 11:00",
    eventsProcessed: 28,
    accuracyDelta: "+0.1%",
    status: "Success" as const,
  },
  {
    id: "CAL-039",
    timestamp: "2026-06-20 22:00",
    eventsProcessed: 51,
    accuracyDelta: "+0.5%",
    status: "Success" as const,
  },
  {
    id: "CAL-038",
    timestamp: "2026-06-20 18:00",
    eventsProcessed: 19,
    accuracyDelta: "-0.1%",
    status: "Warning" as const,
  },
];
