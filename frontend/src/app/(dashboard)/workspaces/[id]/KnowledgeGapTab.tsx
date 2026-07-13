"use client";

import React, { useState, useEffect, useCallback } from "react";
import { api } from "../../../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  TrendingUp,
  FileText,
  Upload,
  ChevronDown,
  ChevronUp,
  Zap,
  AlertCircle,
  ShieldCheck,
  Target,
  BarChart3,
  Sparkles,
  ArrowUp,
  Info,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DeptReport {
  name: string;
  knowledge_pct: number;
  confidence_pct: number;
  missing_documents: string[];
  missing_document_details: { name: string; critical: boolean; reason: string }[];
  critical_knowledge: string[];
  has_critical_missing: boolean;
}

interface GapAnalysis {
  workspace_id: string;
  departments: DeptReport[];
  overall_knowledge_pct: number;
  overall_confidence_pct: number;
  generated_at: string;
}

interface Recommendation {
  document_name: string;
  department: string;
  priority: "critical" | "high" | "medium" | "low";
  reason: string;
  expected_gain_pct: number;
  already_uploaded: boolean;
}

interface RecommendationsData {
  recommendations: Recommendation[];
  upload_priority_queue: Recommendation[];
  total_count: number;
  pending_count: number;
}

interface ReadinessData {
  current: number;
  target: number;
  potential: number;
  breakdown: {
    interview: number;
    documents: number;
    profile: number;
    departments: number;
  };
  gap_to_target: number;
  missing_upload_count: number;
}

interface HealthData {
  status: "Healthy" | "Moderate" | "Poor";
  color: "emerald" | "amber" | "red";
  score: number;
  reasons: string[];
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ReadinessMeter({ readiness }: { readiness: ReadinessData }) {
  const r = 54;
  const circumference = 2 * Math.PI * r;
  const currentOffset = circumference - (circumference * readiness.current) / 100;
  const potentialOffset = circumference - (circumference * readiness.potential) / 100;

  const scoreColor =
    readiness.current >= 75
      ? "#10b981"
      : readiness.current >= 45
      ? "#f59e0b"
      : "#ef4444";

  return (
    <div className="border border-slate-800 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-5">
        <Brain className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white">AI Readiness Score</h3>
        <span className="ml-auto text-[10px] text-slate-500 uppercase tracking-wider font-bold">
          Target: {readiness.target}
        </span>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-8">
        {/* Circular gauge */}
        <div className="relative flex-shrink-0 w-36 h-36">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
            {/* Track */}
            <circle cx="64" cy="64" r={r} fill="none" stroke="#262626" strokeWidth="10" />
            {/* Potential arc */}
            <circle
              cx="64" cy="64" r={r} fill="none"
              stroke="#4f46e5" strokeWidth="10" strokeOpacity="0.25"
              strokeDasharray={circumference}
              strokeDashoffset={potentialOffset}
              strokeLinecap="round"
              style={{ transition: "stroke-dashoffset 1.2s ease" }}
            />
            {/* Current arc */}
            <motion.circle
              cx="64" cy="64" r={r} fill="none"
              stroke={scoreColor} strokeWidth="10"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: currentOffset }}
              transition={{ duration: 1.0, ease: "easeOut" }}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-extrabold text-white leading-none">
              {readiness.current}
            </span>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide mt-0.5">
              / 100
            </span>
          </div>
        </div>

        {/* Breakdown */}
        <div className="flex-1 w-full space-y-3">
          {/* Current vs Target vs Potential */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              { label: "Current", value: readiness.current, color: scoreColor },
              { label: "Target", value: readiness.target, color: "#6366f1" },
              { label: "Potential", value: readiness.potential, color: "#22c55e" },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center"
              >
                <p className="text-[9px] text-slate-500 uppercase tracking-wider font-bold mb-1">
                  {item.label}
                </p>
                <p
                  className="text-xl font-extrabold"
                  style={{ color: item.color }}
                >
                  {item.value}
                </p>
              </div>
            ))}
          </div>

          {/* Factor bars */}
          {Object.entries(readiness.breakdown).map(([key, val]) => {
            const maxes: Record<string, number> = {
              interview: 40,
              documents: 30,
              profile: 15,
              departments: 15,
            };
            const max = maxes[key] || 40;
            const pct = Math.round((val / max) * 100);
            const labels: Record<string, string> = {
              interview: "Interview",
              documents: "Documents",
              profile: "Company Profile",
              departments: "Dept. Coverage",
            };
            return (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-400 font-semibold">{labels[key]}</span>
                  <span className="text-slate-500">
                    {val}/{max} pts ({pct}%)
                  </span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-indigo-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.7, delay: 0.1 }}
                  />
                </div>
              </div>
            );
          })}

          {readiness.gap_to_target > 0 && (
            <p className="text-[10px] text-amber-400 flex items-center gap-1 pt-1">
              <ArrowUp className="w-3 h-3" />
              {readiness.gap_to_target} points needed to reach Production Ready
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function HealthBadge({ health }: { health: HealthData }) {
  const colors: Record<string, { bg: string; border: string; text: string; icon: string }> = {
    emerald: {
      bg: "bg-emerald-950/30",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
      icon: "text-emerald-400",
    },
    amber: {
      bg: "bg-amber-950/30",
      border: "border-amber-500/30",
      text: "text-amber-400",
      icon: "text-amber-400",
    },
    red: {
      bg: "bg-red-950/30",
      border: "border-red-500/30",
      text: "text-red-400",
      icon: "text-red-400",
    },
  };
  const c = colors[health.color] || colors.amber;
  const Icon =
    health.status === "Healthy"
      ? CheckCircle2
      : health.status === "Moderate"
      ? AlertTriangle
      : AlertCircle;

  return (
    <div className={`border ${c.border} ${c.bg} backdrop-blur-md rounded-2xl p-6`}>
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-xl ${c.bg} border ${c.border}`}>
          <Icon className={`w-5 h-5 ${c.icon}`} />
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">
            Knowledge Health
          </p>
          <p className={`text-xl font-extrabold ${c.text}`}>{health.status}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Score</p>
          <p className={`text-2xl font-extrabold ${c.text}`}>{health.score}</p>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-2">
          Why
        </p>
        {health.reasons.map((reason, i) => (
          <div
            key={i}
            className="flex items-start gap-2 text-xs text-slate-300 bg-slate-900/40 rounded-xl px-3 py-2 border border-slate-800"
          >
            <Info className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
            <span className="leading-relaxed">{reason}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DeptKnowledgeCard({ dept }: { dept: DeptReport }) {
  const [expanded, setExpanded] = useState(false);

  const knowledgeColor =
    dept.knowledge_pct >= 75
      ? "from-emerald-500 to-teal-500"
      : dept.knowledge_pct >= 50
      ? "from-amber-500 to-yellow-500"
      : "from-red-500 to-orange-500";

  const knowledgeTextColor =
    dept.knowledge_pct >= 75
      ? "text-emerald-400"
      : dept.knowledge_pct >= 50
      ? "text-amber-400"
      : "text-red-400";

  const confidenceColor =
    dept.confidence_pct >= 70
      ? "text-emerald-400"
      : dept.confidence_pct >= 45
      ? "text-amber-400"
      : "text-red-400";

  return (
    <div className="border border-slate-800 bg-slate-900/20 backdrop-blur-md rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="p-4 flex items-center gap-4">
        {/* Knowledge gauge */}
        <div className="relative w-14 h-14 flex-shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
            <circle cx="28" cy="28" r="22" fill="none" stroke="#262626" strokeWidth="5" />
            <motion.circle
              cx="28" cy="28" r="22" fill="none"
              className={`stroke-current ${knowledgeTextColor}`}
              strokeWidth="5"
              strokeDasharray={`${2 * Math.PI * 22}`}
              initial={{ strokeDashoffset: `${2 * Math.PI * 22}` }}
              animate={{
                strokeDashoffset: `${2 * Math.PI * 22 - (2 * Math.PI * 22 * dept.knowledge_pct) / 100}`,
              }}
              transition={{ duration: 0.8 }}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-xs font-extrabold ${knowledgeTextColor}`}>
              {dept.knowledge_pct}%
            </span>
          </div>
        </div>

        {/* Name & metrics */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-bold text-white truncate">{dept.name}</h4>
            {dept.has_critical_missing && (
              <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-red-500/10 border border-red-500/20 text-red-400">
                <AlertCircle className="w-2.5 h-2.5" /> Critical Gap
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-[10px]">
            <span className="text-slate-500">
              Knowledge:{" "}
              <span className={`font-bold ${knowledgeTextColor}`}>
                {dept.knowledge_pct}%
              </span>
            </span>
            <span className="text-slate-500">
              Confidence:{" "}
              <span className={`font-bold ${confidenceColor}`}>
                {dept.confidence_pct}%
              </span>
            </span>
          </div>
          {/* Knowledge bar */}
          <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full bg-gradient-to-r ${knowledgeColor}`}
              initial={{ width: 0 }}
              animate={{ width: `${dept.knowledge_pct}%` }}
              transition={{ duration: 0.8 }}
            />
          </div>
        </div>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all flex-shrink-0"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Expanded section */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-slate-800"
          >
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Missing Documents */}
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                  <FileText className="w-3 h-3" /> Missing Documents
                </p>
                {dept.missing_document_details.length > 0 ? (
                  <div className="space-y-1.5">
                    {dept.missing_document_details.slice(0, 4).map((doc, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 text-[10px] text-slate-400"
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${
                            doc.critical ? "bg-red-400" : "bg-amber-400"
                          }`}
                        />
                        <span className="leading-relaxed">{doc.name}</span>
                      </div>
                    ))}
                    {dept.missing_document_details.length > 4 && (
                      <p className="text-[10px] text-slate-600 italic">
                        +{dept.missing_document_details.length - 4} more
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> All key documents uploaded
                  </p>
                )}
              </div>

              {/* Critical Knowledge Gaps */}
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Critical Knowledge
                </p>
                {dept.critical_knowledge.length > 0 ? (
                  <div className="space-y-1.5">
                    {dept.critical_knowledge.slice(0, 4).map((gap, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 text-[10px] text-slate-400"
                      >
                        <AlertCircle className="w-3 h-3 text-red-400 flex-shrink-0 mt-0.5" />
                        <span className="leading-relaxed capitalize">{gap}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Core knowledge covered
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

const PRIORITY_CONFIG = {
  critical: {
    label: "Critical",
    bg: "bg-red-950/40",
    border: "border-red-500/30",
    badge: "bg-red-500/20 border-red-500/40 text-red-300",
    dot: "bg-red-400",
  },
  high: {
    label: "High",
    bg: "bg-amber-950/20",
    border: "border-amber-500/20",
    badge: "bg-amber-500/20 border-amber-500/40 text-amber-300",
    dot: "bg-amber-400",
  },
  medium: {
    label: "Medium",
    bg: "bg-slate-900/20",
    border: "border-slate-700",
    badge: "bg-indigo-500/10 border-indigo-500/30 text-indigo-300",
    dot: "bg-indigo-400",
  },
  low: {
    label: "Low",
    bg: "bg-slate-900/10",
    border: "border-slate-800",
    badge: "bg-slate-700/50 border-slate-600 text-slate-400",
    dot: "bg-slate-500",
  },
};

function RecommendationCard({ rec, index }: { rec: Recommendation; index: number }) {
  const cfg = PRIORITY_CONFIG[rec.priority] || PRIORITY_CONFIG.medium;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.04 }}
      className={`border ${cfg.border} ${cfg.bg} backdrop-blur-md rounded-2xl p-4 relative overflow-hidden`}
    >
      {/* Priority stripe */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${cfg.dot}`} />

      <div className="pl-3">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h4 className="text-sm font-bold text-white truncate">{rec.document_name}</h4>
              {rec.already_uploaded && (
                <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Uploaded
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${cfg.badge}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                {cfg.label}
              </span>
              <span className="text-[10px] text-slate-500 font-semibold bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full">
                {rec.department}
              </span>
            </div>
          </div>

          {/* Expected gain */}
          <div className="flex-shrink-0 text-right bg-slate-950 border border-slate-800 rounded-xl px-3 py-2">
            <p className="text-[9px] text-slate-500 uppercase tracking-wider font-bold">
              AI Gain
            </p>
            <p className="text-base font-extrabold text-emerald-400">
              +{rec.expected_gain_pct}%
            </p>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed">{rec.reason}</p>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function KnowledgeGapTab({ workspaceId }: { workspaceId: string }) {
  const [analysis, setAnalysis] = useState<GapAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationsData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeSection, setActiveSection] = useState<
    "overview" | "departments" | "recommendations" | "upload"
  >("overview");

  const [recFilter, setRecFilter] = useState<"all" | "critical" | "high" | "medium">("all");
  const [showUploaded, setShowUploaded] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analysisRes, recsRes, readinessRes, healthRes] = await Promise.all([
        api.get(`/knowledge-gap/${workspaceId}/analysis`),
        api.get(`/knowledge-gap/${workspaceId}/recommendations`),
        api.get(`/knowledge-gap/${workspaceId}/readiness`),
        api.get(`/knowledge-gap/${workspaceId}/health`),
      ]);
      setAnalysis(analysisRes.data);
      setRecommendations(recsRes.data);
      setReadiness(readinessRes.data);
      setHealth(healthRes.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load knowledge gap analysis.");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
            <Brain className="w-8 h-8 text-indigo-400" />
          </div>
          <div className="absolute inset-0 rounded-2xl border-2 border-indigo-500/30 animate-ping" />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-white">Analyzing Knowledge Gaps...</p>
          <p className="text-xs text-slate-500 mt-1">
            Scanning interview data, documents, and company profile
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <AlertCircle className="w-12 h-12 text-red-400" />
        <div className="text-center">
          <p className="text-sm font-semibold text-white mb-1">Analysis Failed</p>
          <p className="text-xs text-slate-500 max-w-sm leading-normal">{error}</p>
        </div>
        <button
          onClick={fetchAll}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition-all flex items-center gap-2"
        >
          <Loader2 className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  // ── Filter recommendations ────────────────────────────────────────────────
  const filteredRecs = (recommendations?.recommendations || []).filter((r) => {
    if (!showUploaded && r.already_uploaded) return false;
    if (recFilter !== "all" && r.priority !== recFilter) return false;
    return true;
  });

  const uploadQueue = recommendations?.upload_priority_queue || [];

  // ── Section tabs ──────────────────────────────────────────────────────────
  const sections = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "departments", label: "Departments", icon: Target },
    { key: "recommendations", label: "Recommendations", icon: Sparkles },
    { key: "upload", label: "Upload Priority", icon: Upload },
  ] as const;

  return (
    <div className="glass-card p-6 md:p-8 space-y-6 animate-in fade-in duration-200 max-w-6xl mx-auto">
      {/* Section Nav */}
      <div className="flex bg-slate-900/60 border border-slate-800 p-1 rounded-xl w-full overflow-x-auto shadow-inner">
        {sections.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveSection(key)}
            className={`flex-1 min-w-fit px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 whitespace-nowrap ${
              activeSection === key
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* ── OVERVIEW ───────────────────────────────────────────────────── */}
        {activeSection === "overview" && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-6"
          >
            {/* Top stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                {
                  label: "Overall Knowledge",
                  value: `${analysis?.overall_knowledge_pct ?? 0}%`,
                  sub: "Across all departments",
                  color: "text-indigo-400",
                },
                {
                  label: "AI Confidence",
                  value: `${analysis?.overall_confidence_pct ?? 0}%`,
                  sub: "Answer accuracy estimate",
                  color: "text-purple-400",
                },
                {
                  label: "Departments Analysed",
                  value: `${analysis?.departments?.length ?? 0}`,
                  sub: "Distinct knowledge areas",
                  color: "text-cyan-400",
                },
                {
                  label: "Pending Uploads",
                  value: `${recommendations?.pending_count ?? 0}`,
                  sub: "Recommended documents",
                  color: "text-amber-400",
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="border border-slate-800 bg-slate-900/20 backdrop-blur-md rounded-2xl p-4"
                >
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-2">
                    {stat.label}
                  </p>
                  <p className={`text-3xl font-extrabold ${stat.color}`}>{stat.value}</p>
                  <p className="text-[10px] text-slate-600 mt-1 leading-relaxed">{stat.sub}</p>
                </div>
              ))}
            </div>

            {/* Readiness + Health row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                {readiness && <ReadinessMeter readiness={readiness} />}
              </div>
              <div>{health && <HealthBadge health={health} />}</div>
            </div>

            {/* Department snapshot */}
            {analysis && analysis.departments.length > 0 && (
              <div className="border border-slate-800 bg-slate-900/20 backdrop-blur-md rounded-2xl p-6">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h3 className="text-sm font-bold text-white">Department Knowledge Snapshot</h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Quick view — click Departments tab for details
                    </p>
                  </div>
                </div>
                <div className="space-y-3">
                  {analysis.departments.slice(0, 5).map((dept) => {
                    const color =
                      dept.knowledge_pct >= 75
                        ? "bg-emerald-500"
                        : dept.knowledge_pct >= 50
                        ? "bg-amber-500"
                        : "bg-red-500";
                    return (
                      <div key={dept.name} className="space-y-1">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300 flex items-center gap-2">
                            {dept.name}
                            {dept.has_critical_missing && (
                              <AlertCircle className="w-3 h-3 text-red-400" />
                            )}
                          </span>
                          <span className="text-slate-500 font-semibold">
                            {dept.knowledge_pct}% knowledge · {dept.confidence_pct}% confidence
                          </span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full rounded-full ${color}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${dept.knowledge_pct}%` }}
                            transition={{ duration: 0.7 }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
                {analysis.departments.length > 5 && (
                  <button
                    onClick={() => setActiveSection("departments")}
                    className="mt-4 text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    <ChevronDown className="w-3 h-3" />
                    View all {analysis.departments.length} departments
                  </button>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* ── DEPARTMENTS ─────────────────────────────────────────────────── */}
        {activeSection === "departments" && (
          <motion.div
            key="departments"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-4"
          >
            <div>
              <h3 className="text-base font-bold text-white">Department Knowledge Analysis</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Per-department knowledge %, confidence %, missing documents, and critical gaps
              </p>
            </div>

            {analysis && analysis.departments.length > 0 ? (
              <div className="space-y-3">
                {analysis.departments.map((dept) => (
                  <DeptKnowledgeCard key={dept.name} dept={dept} />
                ))}
              </div>
            ) : (
              <div className="border border-dashed border-slate-800 rounded-2xl p-16 text-center flex flex-col items-center">
                <Brain className="w-12 h-12 text-slate-700 mb-4" />
                <p className="text-sm font-semibold text-slate-300">No department data yet</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm leading-normal">
                  Complete the AI onboarding interview to generate department-level knowledge analysis.
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* ── RECOMMENDATIONS ─────────────────────────────────────────────── */}
        {activeSection === "recommendations" && (
          <motion.div
            key="recommendations"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-5"
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Document Recommendation Engine</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  AI-generated upload suggestions based on interview and company profile
                </p>
              </div>
              {/* Filters */}
              <div className="flex items-center gap-2 flex-wrap">
                {(["all", "critical", "high", "medium"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setRecFilter(f)}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-all border ${
                      recFilter === f
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {f}
                  </button>
                ))}
                <button
                  onClick={() => setShowUploaded(!showUploaded)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-all border ${
                    showUploaded
                      ? "bg-emerald-800/50 border-emerald-700 text-emerald-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {showUploaded ? "Hide" : "Show"} Uploaded
                </button>
              </div>
            </div>

            {filteredRecs.length > 0 ? (
              <div className="space-y-3">
                {filteredRecs.map((rec, i) => (
                  <RecommendationCard key={`${rec.document_name}-${rec.department}`} rec={rec} index={i} />
                ))}
              </div>
            ) : (
              <div className="border border-dashed border-slate-800 rounded-2xl p-16 text-center flex flex-col items-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-4" />
                <p className="text-sm font-semibold text-slate-300">
                  {recFilter !== "all"
                    ? `No ${recFilter} priority recommendations`
                    : "No pending recommendations"}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {recFilter !== "all" ? "Try changing the filter." : "All suggested documents are uploaded."}
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* ── UPLOAD PRIORITY ─────────────────────────────────────────────── */}
        {activeSection === "upload" && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-5"
          >
            <div>
              <h3 className="text-base font-bold text-white">Upload Priority Queue</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                The top documents to upload next for the highest AI knowledge improvement
              </p>
            </div>

            {uploadQueue.length > 0 ? (
              <div className="space-y-3">
                {uploadQueue.map((rec, i) => {
                  const cfg = PRIORITY_CONFIG[rec.priority] || PRIORITY_CONFIG.medium;
                  return (
                    <motion.div
                      key={`${rec.document_name}-${i}`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: i * 0.05 }}
                      className={`border ${cfg.border} ${cfg.bg} rounded-2xl p-4 flex items-start gap-4`}
                    >
                      {/* Rank number */}
                      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center">
                        <span className="text-xs font-extrabold text-slate-400">#{i + 1}</span>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3 mb-1">
                          <h4 className="text-sm font-bold text-white">{rec.document_name}</h4>
                          <span
                            className={`flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${cfg.badge}`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                            {cfg.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-[10px] text-slate-500 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-full font-semibold">
                            {rec.department}
                          </span>
                          <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            +{rec.expected_gain_pct}% AI knowledge gain
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{rec.reason}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <div className="border border-dashed border-slate-800 rounded-2xl p-16 text-center flex flex-col items-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-4" />
                <p className="text-sm font-semibold text-slate-300">Upload Queue is Empty</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm leading-normal">
                  All suggested priority documents appear to already be uploaded. Great work!
                </p>
              </div>
            )}

            {/* Summary card */}
            {uploadQueue.length > 0 && readiness && (
              <div className="border border-indigo-500/20 bg-indigo-950/20 rounded-2xl p-5">
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-white mb-1">
                      Upload all {uploadQueue.length} documents to reach{" "}
                      <span className="text-indigo-400">{readiness.potential}% readiness</span>
                    </p>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Uploading the priority queue could improve your AI readiness from{" "}
                      <strong className="text-white">{readiness.current}</strong> to{" "}
                      <strong className="text-indigo-300">{readiness.potential}</strong> — a gain of{" "}
                      <strong className="text-emerald-400">
                        +{readiness.potential - readiness.current} points
                      </strong>
                      .
                    </p>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
