"use client";

import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { api } from "../../../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Brain,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  FileText,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ShieldAlert,
  Activity,
  Network,
  FileSearch,
  Zap,
  AlertCircle,
  RotateCcw,
  MessageSquare,
  Bot,
  Star,
  TrendingUp,
  Wrench,
  ClipboardCheck,
  BookOpen,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Citation {
  document_id: string;
  title: string;
  page_number: number;
  section: string;
  chunk_id: string;
  excerpt: string;
  score: number;
  stars: number;
  source_type: "document" | "interview" | "profile";
}

interface FailurePattern {
  equipment: string;
  pattern: string;
  occurrences: number;
  source_documents: string[];
}

interface ComplianceSignal {
  standard: string;
  status: "present" | "missing" | "partial";
  note: string;
}

interface SourcesConsulted {
  documents_searched: number;
  chunks_retrieved: number;
  interview_answers_checked: number;
  graph_entities_matched: number;
  company_profile_used: boolean;
  response_time_ms: number;
}

interface CopilotResponse {
  answer: string;
  reasoning: string;
  confidence: number;
  risk_level: "none" | "low" | "medium" | "high";
  knowledge_missing: boolean;
  missing_explanation: string | null;
  citations: Citation[];
  failure_patterns: FailurePattern[];
  risk_signals: string[];
  recommended_actions: string[];
  compliance_signals: ComplianceSignal[];
  sources_consulted: SourcesConsulted;
  related: { equipment: string[]; departments: string[]; standards: string[] };
  suggestions: string[];
  session_id: string;
}

interface ConversationEntry {
  userMessage: string;
  response: CopilotResponse;
  id: string;
}

interface DocumentItem {
  id: string;
  name: string;
  status: string;
  department: string | null;
}

interface CopilotTabProps {
  workspaceId: string;
  documents: DocumentItem[];
}

// ─── Thinking stages ─────────────────────────────────────────────────────────

const THINKING_STAGES = [
  { icon: FileSearch, label: "Searching documents..." },
  { icon: Network, label: "Traversing knowledge graph..." },
  { icon: Brain, label: "Connecting knowledge..." },
  { icon: AlertTriangle, label: "Assessing operational risk..." },
  { icon: Sparkles, label: "Generating response..." },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function StarRating({ stars }: { stars: number }) {
  return (
    <span className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star
          key={s}
          className={`w-3 h-3 ${s <= stars ? "text-amber-400 fill-amber-400" : "text-slate-700"}`}
        />
      ))}
    </span>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const color =
    confidence >= 80
      ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
      : confidence >= 50
      ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
      : "text-red-400 border-red-500/30 bg-red-500/10";
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${color}`}>
      <Activity className="w-3 h-3" />
      {confidence}% Confidence
    </span>
  );
}

function RiskBadge({ level }: { level: string }) {
  if (level === "none") return null;
  const map: Record<string, string> = {
    high: "text-red-400 border-red-500/30 bg-red-500/10",
    medium: "text-amber-400 border-amber-500/30 bg-amber-500/10",
    low: "text-blue-400 border-blue-500/30 bg-blue-500/10",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${map[level] || ""}`}>
      <AlertTriangle className="w-3 h-3" />
      {level.toUpperCase()} RISK
    </span>
  );
}

function SourcesPanel({ sources }: { sources: SourcesConsulted }) {
  return (
    <div className="bg-slate-950 border border-slate-800/60 rounded-xl p-4 mt-3">
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">
        OperationalBrain Consulted
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {[
          { label: "Documents", value: sources.documents_searched, icon: FileText },
          { label: "Chunks", value: sources.chunks_retrieved, icon: BookOpen },
          { label: "Interview Answers", value: sources.interview_answers_checked, icon: MessageSquare },
          { label: "Graph Entities", value: sources.graph_entities_matched, icon: Network },
          { label: "Company Profile", value: sources.company_profile_used ? "✓" : "—", icon: Brain },
          { label: "Response Time", value: `${(sources.response_time_ms / 1000).toFixed(1)}s`, icon: Zap },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-center gap-2 bg-slate-900/50 rounded-lg p-2">
            <Icon className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
            <div>
              <p className="text-[10px] text-slate-500">{label}</p>
              <p className="text-xs font-bold text-slate-200">{value}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);
  const isInterview = citation.source_type === "interview";
  return (
    <div className="border border-slate-800/60 rounded-xl overflow-hidden bg-slate-950/50">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-900/40 transition-colors text-left"
      >
        <StarRating stars={citation.stars} />
        <span className="flex-1 text-xs font-semibold text-slate-300 truncate">
          {isInterview ? (
            <span className="text-indigo-400">[Interview] </span>
          ) : null}
          {citation.title}
          {citation.page_number > 0 && !isInterview && (
            <span className="text-slate-500 ml-1">p.{citation.page_number}</span>
          )}
        </span>
        <span className="text-[10px] text-slate-600">
          {(citation.score * 100).toFixed(0)}%
        </span>
        {open ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        )}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1 border-t border-slate-800/40">
              <p className="text-xs text-slate-400 italic leading-relaxed">
                "{citation.excerpt}"
              </p>
              {citation.section && (
                <p className="text-[10px] text-slate-600 mt-1.5">
                  Section: {citation.section}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResponseCard({ entry, isDemoMode = true }: { entry: ConversationEntry, isDemoMode?: boolean }) {
  const { response } = entry;
  
  // Demo mode staggered animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: isDemoMode ? 0.3 : 0.1 }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  const hasRisk = response.risk_level !== "none";
  const hasFailures = response.failure_patterns.length > 0;
  const hasCompliance = response.compliance_signals.length > 0;
  
  // Calculate unique documents used
  const uniqueDocs = Array.from(new Set(response.citations.filter(c => c.source_type === 'document').map(c => c.title)));
  const multipleDocs = uniqueDocs.length > 1;

  return (
    <motion.div 
      className="space-y-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* 1. SUMMARY */}
      <motion.div variants={itemVariants} className="bg-slate-900/50 border border-slate-800/80 rounded-xl overflow-hidden shadow-lg">
        <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-black uppercase tracking-widest text-slate-400">Executive Summary</span>
          </div>
          <ConfidenceBadge confidence={response.confidence} />
        </div>
        <div className="p-5 prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed font-medium">
          {response.knowledge_missing ? (
            <div>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{response.answer}</ReactMarkdown>
              {response.missing_explanation && (
                <p className="text-xs text-slate-500 mt-2 italic bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                  {response.missing_explanation}
                </p>
              )}
            </div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{response.answer}</ReactMarkdown>
          )}
        </div>
      </motion.div>

      {/* 2. EVIDENCE */}
      {response.citations.length > 0 && (
        <motion.div variants={itemVariants} className="bg-slate-950 border border-slate-800/50 rounded-xl overflow-hidden">
          <div className="px-4 py-2 bg-emerald-950/20 border-b border-emerald-900/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-black uppercase tracking-widest text-emerald-400/80">Grounding Evidence</span>
            </div>
          </div>
          <div className="p-4 space-y-3">
            {multipleDocs && (
              <div className="mb-4 inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-300 text-xs font-bold">
                <Network className="w-3.5 h-3.5" />
                Combined knowledge from {uniqueDocs.length} uploaded documents
              </div>
            )}
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {response.citations.map((c, i) => (
                <div key={i} className="bg-slate-900 border border-slate-800 rounded-lg p-3 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-1 h-full bg-emerald-500/30" />
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold text-slate-300 truncate pr-4">{c.title}</span>
                    <span className="text-[10px] text-emerald-500/80 font-mono bg-emerald-500/10 px-1.5 rounded">{(c.score * 100).toFixed(0)}% match</span>
                  </div>
                  <p className="text-[11px] text-slate-400 italic line-clamp-3 mb-2 leading-relaxed">"{c.excerpt}"</p>
                  <div className="flex gap-2 text-[10px] text-slate-500 font-mono">
                    {c.page_number > 0 && <span className="bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">Page {c.page_number}</span>}
                    {c.section && <span className="bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 truncate">{c.section}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 3. POSSIBLE CAUSES */}
        {hasFailures && (
          <motion.div variants={itemVariants} className="border border-orange-500/20 bg-orange-950/10 rounded-xl overflow-hidden">
             <div className="px-4 py-2 border-b border-orange-500/10 flex items-center gap-2 bg-orange-950/20">
              <TrendingUp className="w-4 h-4 text-orange-400" />
              <span className="text-xs font-black uppercase tracking-widest text-orange-400/80">Possible Causes</span>
            </div>
            <div className="p-4 space-y-3">
              {response.failure_patterns.map((fp, i) => (
                <div key={i} className="bg-slate-900/50 rounded p-2.5 border border-slate-800">
                  <p className="text-xs font-bold text-orange-300 mb-1">{fp.pattern}</p>
                  <p className="text-[10px] text-slate-500 font-mono flex items-center gap-1.5">
                    <FileText className="w-3 h-3" />
                    {fp.source_documents.join(", ")}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* 4. RECOMMENDATIONS */}
        {response.recommended_actions.length > 0 && (
          <motion.div variants={itemVariants} className="border border-blue-500/20 bg-blue-950/10 rounded-xl overflow-hidden">
             <div className="px-4 py-2 border-b border-blue-500/10 flex items-center gap-2 bg-blue-950/20">
              <ClipboardCheck className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-black uppercase tracking-widest text-blue-400/80">Recommendations</span>
            </div>
            <div className="p-4">
              <ol className="space-y-2">
                {response.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded border border-slate-800/50">
                    <span className="text-blue-500 font-black mt-0.5">{i + 1}.</span>
                    <span className="leading-relaxed">{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          </motion.div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 5. SAFETY */}
        {hasRisk && response.risk_signals.length > 0 && (
          <motion.div variants={itemVariants} className="border border-red-500/20 bg-red-950/10 rounded-xl overflow-hidden">
            <div className="px-4 py-2 border-b border-red-500/10 flex items-center justify-between bg-red-950/20">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                <span className="text-xs font-black uppercase tracking-widest text-red-400/80">Safety Signals</span>
              </div>
              <RiskBadge level={response.risk_level} />
            </div>
            <div className="p-4">
              <ul className="space-y-2">
                {response.risk_signals.map((sig, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-2 bg-slate-900/40 p-2 rounded border border-red-900/30">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-500/70 mt-0.5 shrink-0" />
                    <span>{sig}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}

        {/* 6. COMPLIANCE */}
        {hasCompliance && (
          <motion.div variants={itemVariants} className="border border-purple-500/20 bg-purple-950/10 rounded-xl overflow-hidden">
            <div className="px-4 py-2 border-b border-purple-500/10 flex items-center gap-2 bg-purple-950/20">
              <CheckCircle2 className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-black uppercase tracking-widest text-purple-400/80">Compliance Check</span>
            </div>
            <div className="p-4 space-y-2">
              {response.compliance_signals.map((cs, i) => (
                <div key={i} className="flex items-start gap-2.5 bg-slate-900/40 p-2.5 rounded border border-slate-800">
                  {cs.status === "present" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-bold text-slate-300">{cs.standard}</span>
                      <span className={`text-[9px] font-black uppercase tracking-wider px-1.5 rounded ${cs.status === "present" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                        {cs.status === "present" ? "Present" : "Missing"}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500">{cs.note}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* 7. RELATED DOCUMENTS / METADATA */}
      <motion.div variants={itemVariants}>
        {(response.related.equipment.length > 0 ||
          response.related.departments.length > 0 ||
          response.related.standards.length > 0) && (
          <div className="flex flex-wrap gap-2 py-2">
            {response.related.equipment.map((e) => (
              <span key={e} className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-900 text-slate-300 border border-slate-800">
                <Wrench className="w-3 h-3 inline mr-1.5 opacity-70" />
                {e}
              </span>
            ))}
            {response.related.departments.map((d) => (
              <span key={d} className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-900/20 text-indigo-300 border border-indigo-800/30">
                {d}
              </span>
            ))}
            {response.related.standards.map((s) => (
              <span key={s} className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-purple-900/20 text-purple-300 border border-purple-800/30">
                {s}
              </span>
            ))}
          </div>
        )}
      </motion.div>
      {/* Follow-up chips */}
      {response.suggestions.length > 0 && (
        <div className="pt-1">
          <p className="text-[10px] text-slate-600 mb-1.5">Follow-up questions:</p>
          <div className="flex flex-wrap gap-2">
            {response.suggestions.map((s, i) => (
              <button
                key={i}
                className="text-[11px] text-indigo-300 border border-indigo-800/40 bg-indigo-900/20 hover:bg-indigo-900/40 rounded-full px-3 py-1 transition-colors"
                data-suggestion={s}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function ThinkingAnimation({ stage }: { stage: number }) {
  return (
    <div className="flex flex-col gap-2 py-2">
      {THINKING_STAGES.map((s, i) => {
        const Icon = s.icon;
        const active = i === stage;
        const done = i < stage;
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.12 }}
            className={`flex items-center gap-2.5 text-xs transition-colors ${
              done
                ? "text-emerald-500"
                : active
                ? "text-indigo-300"
                : "text-slate-700"
            }`}
          >
            {done ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            ) : active ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            ) : (
              <Icon className="w-3.5 h-3.5" />
            )}
            {s.label}
          </motion.div>
        );
      })}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CopilotTab({ workspaceId, documents }: CopilotTabProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingStage, setThinkingStage] = useState(0);
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Document context mode
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [docContextOpen, setDocContextOpen] = useState(false);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const thinkingInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Only show ready docs in the selector
  const readyDocs = documents.filter((d) => d.status === "ready");
  const selectedDoc = readyDocs.find((d) => d.id === selectedDocId);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation, loading]);

  // Wire up suggestion chips after render
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const btn = (e.target as HTMLElement).closest("[data-suggestion]");
      if (btn) {
        const text = (btn as HTMLElement).dataset.suggestion || "";
        setInput(text);
        inputRef.current?.focus();
      }
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, []);

  const startThinking = () => {
    setThinkingStage(0);
    thinkingInterval.current = setInterval(() => {
      setThinkingStage((prev) => {
        if (prev < THINKING_STAGES.length - 1) return prev + 1;
        return prev;
      });
    }, 600);
  };

  const stopThinking = () => {
    if (thinkingInterval.current) {
      clearInterval(thinkingInterval.current);
      thinkingInterval.current = null;
    }
  };

  const handleSend = useCallback(async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setError(null);
    setLoading(true);
    startThinking();

    try {
      const body: any = {
        message: msg,
        session_id: sessionId,
      };

      if (selectedDocId && selectedDoc) {
        body.document_context = {
          document_id: selectedDocId,
          document_name: selectedDoc.name,
          excerpt: "",
        };
      }

      const res = await api.post(`/copilot/${workspaceId}/query`, body);
      const data: CopilotResponse = res.data;

      if (data.session_id) setSessionId(data.session_id);

      setConversation((prev) => [
        ...prev,
        { userMessage: msg, response: data, id: `${Date.now()}` },
      ]);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Failed to reach the OperationalBrain Expert. Please check the backend is running."
      );
    } finally {
      stopThinking();
      setLoading(false);
    }
  }, [input, loading, sessionId, workspaceId, selectedDocId, selectedDoc]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      if (sessionId) {
        await api.delete(`/copilot/${workspaceId}/history`);
      }
    } catch (_) {}
    setConversation([]);
    setSessionId(null);
    setError(null);
  };

  const hasConversation = conversation.length > 0;

  return (
    <div className="glass-card p-6 md:p-8 flex flex-col h-full min-h-[70vh] max-w-5xl mx-auto">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pb-5 border-b border-slate-900 mb-5">
        <div className="flex items-center gap-4">
          {/* AI Avatar */}
          <div className="relative flex-shrink-0">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center shadow-[0_0_24px_rgba(99,102,241,0.4)]">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-slate-950 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-white tracking-tight">
              OperationalBrain Expert
            </h2>
            <p className="text-xs text-slate-500">
              Industrial AI Reasoning Agent · Powered by your documents
            </p>
          </div>
        </div>
        {hasConversation && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-900"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Clear
          </button>
        )}
      </div>

      {/* ── Document context selector ───────────────────────────────────── */}
      {readyDocs.length > 0 && (
        <div className="mb-5">
          <button
            onClick={() => setDocContextOpen((v) => !v)}
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <FileSearch className="w-3.5 h-3.5 text-indigo-400" />
            {selectedDoc ? (
              <span>
                Asking about:{" "}
                <span className="text-indigo-300 font-semibold">{selectedDoc.name}</span>
                <span className="ml-2 text-slate-600">(click to change)</span>
              </span>
            ) : (
              "Ask about a specific document"
            )}
            {docContextOpen ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
          <AnimatePresence>
            {docContextOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <button
                    onClick={() => { setSelectedDocId(""); setDocContextOpen(false); }}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-left border transition-colors ${
                      !selectedDocId
                        ? "border-indigo-600/50 bg-indigo-900/20 text-indigo-300"
                        : "border-slate-800 bg-slate-900/30 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <Brain className="w-3.5 h-3.5 flex-shrink-0" />
                    All knowledge (default)
                  </button>
                  {readyDocs.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => { setSelectedDocId(doc.id); setDocContextOpen(false); }}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-left border transition-colors truncate ${
                        selectedDocId === doc.id
                          ? "border-indigo-600/50 bg-indigo-900/20 text-indigo-300"
                          : "border-slate-800 bg-slate-900/30 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5 flex-shrink-0 text-indigo-400" />
                      <span className="truncate">{doc.name}</span>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* ── Conversation area ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-8 mb-5 pr-1">
        {/* Empty state */}
        {!hasConversation && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-600/20 to-purple-700/20 border border-indigo-700/20 flex items-center justify-center mx-auto mb-4">
              <Brain className="w-8 h-8 text-indigo-400" />
            </div>
            <h3 className="text-base font-bold text-slate-300 mb-2">
              Ask me anything about your operations
            </h3>
            <p className="text-xs text-slate-600 max-w-md mx-auto mb-6">
              I reason across your uploaded documents, interview knowledge, and
              operational profile. I detect risks, surface failure patterns, and
              recommend actions.
            </p>
            {/* Starter chips */}
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                "How is preventive maintenance performed?",
                "What safety procedures are documented?",
                "Which SOPs are missing?",
                "Summarize the maintenance procedures",
                "Are there any compliance gaps?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-[11px] text-slate-400 border border-slate-800 bg-slate-900/40 hover:bg-slate-900 hover:text-slate-200 rounded-full px-3 py-1.5 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Conversation entries */}
        {conversation.map((entry) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            {/* User bubble */}
            <div className="flex justify-end">
              <div className="max-w-[80%] bg-indigo-700/30 border border-indigo-700/30 rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm text-indigo-100">
                {entry.userMessage}
              </div>
            </div>

            {/* Assistant response */}
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-[0_0_12px_rgba(99,102,241,0.3)]">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <ResponseCard entry={entry} />
              </div>
            </div>
          </motion.div>
        ))}

        {/* Thinking animation */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center flex-shrink-0 shadow-[0_0_12px_rgba(99,102,241,0.3)]">
              <Bot className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl rounded-tl-sm px-4 py-3">
              <ThinkingAnimation stage={thinkingStage} />
            </div>
          </motion.div>
        )}

        {/* Error */}
        {error && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-xl bg-red-900/50 border border-red-800/50 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-3.5 h-3.5 text-red-400" />
            </div>
            <div className="bg-red-950/20 border border-red-800/30 rounded-xl px-4 py-3">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ──────────────────────────────────────────────────── */}
      <div className="border-t border-slate-900 pt-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-2xl focus-within:border-indigo-700/60 focus-within:ring-1 focus-within:ring-indigo-700/30 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
              }}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
              placeholder={
                selectedDoc
                  ? `Ask me anything about ${selectedDoc.name}...`
                  : "Ask about maintenance, safety, compliance, equipment…"
              }
              className="w-full bg-transparent px-4 py-3 text-sm text-slate-200 placeholder-slate-600 resize-none outline-none leading-relaxed"
              style={{ minHeight: "44px", maxHeight: "120px" }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-11 h-11 flex-shrink-0 flex items-center justify-center rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-[0_0_16px_rgba(99,102,241,0.3)] hover:shadow-[0_0_24px_rgba(99,102,241,0.5)]"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        </div>
        <p className="text-[10px] text-slate-700 mt-2 text-center">
          Enter to send · Shift+Enter for new line · Answers grounded in your uploaded documents
        </p>
      </div>
    </div>
  );
}
