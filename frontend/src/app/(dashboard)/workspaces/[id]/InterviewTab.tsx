"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, formatError } from "../../../../lib/api";
import { useAuth } from "../../../../context/AuthContext";
import {
  Brain,
  Send,
  CheckCircle2,
  Loader2,
  ClipboardList,
  Building2,
  ChevronRight,
  FileText,
  AlertCircle,
  Star,
  Zap,
  TrendingUp,
  Award,
  BarChart3,
  BookOpen,
  Shield,
  Wrench,
  Users,
  DollarSign,
  Globe,
  Cpu,
  Truck,
  FlaskConical,
  GraduationCap,
  ArrowRight,
  Sparkles,
  Info,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: "ai" | "user";
  content: string;
  department?: string;
  category?: string;
  timestamp: Date;
  isTyping?: boolean;
}

interface Progress {
  progress: Record<string, number>;
  completion_percentage: number;
  current_department: string | null;
  knowledge_score: number;
  department_confidence: Record<string, number>;
  missing_info: string[];
  questions_asked: number;
  questions_answered: number;
}

interface Recommendation {
  document_name: string;
  priority: "high" | "medium" | "low";
  reason: string;
}

interface DeptRecommendation {
  department: string;
  documents: Recommendation[];
}

type ViewState = "loading" | "start" | "chat" | "completing" | "completed" | "recommendations";

// ─── Department icons ─────────────────────────────────────────────────────────

const DEPT_ICONS: Record<string, React.ReactNode> = {
  General: <Globe className="w-3.5 h-3.5" />,
  Production: <Cpu className="w-3.5 h-3.5" />,
  Quality: <Award className="w-3.5 h-3.5" />,
  Maintenance: <Wrench className="w-3.5 h-3.5" />,
  Safety: <Shield className="w-3.5 h-3.5" />,
  HR: <Users className="w-3.5 h-3.5" />,
  Finance: <DollarSign className="w-3.5 h-3.5" />,
  Procurement: <Truck className="w-3.5 h-3.5" />,
  Clinical: <FlaskConical className="w-3.5 h-3.5" />,
  Academic: <GraduationCap className="w-3.5 h-3.5" />,
  Engineering: <Cpu className="w-3.5 h-3.5" />,
  Operations: <BarChart3 className="w-3.5 h-3.5" />,
  "Risk & Compliance": <Shield className="w-3.5 h-3.5" />,
  "Safety & HSE": <Shield className="w-3.5 h-3.5" />,
};

const getDeptIcon = (dept: string) =>
  DEPT_ICONS[dept] ?? <BarChart3 className="w-3.5 h-3.5" />;

const PRIORITY_COLORS = {
  high: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", label: "High" },
  medium: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", label: "Medium" },
  low: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400", label: "Low" },
};

// ─── Typing animation component ───────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-indigo-400"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </div>
  );
}

// ─── Typewriter component ─────────────────────────────────────────────────────

function TypewriterText({ text, onDone }: { text: string; onDone?: () => void }) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    let i = 0;
    // Speed: instant for short text, slightly staggered for long
    const delay = text.length > 200 ? 8 : text.length > 80 ? 12 : 16;
    intervalRef.current = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(intervalRef.current!);
        setDone(true);
        onDone?.();
      }
    }, delay);
    return () => clearInterval(intervalRef.current!);
  }, [text]);

  // Render markdown-lite: bold with **
  const renderText = (raw: string) => {
    const parts = raw.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="text-white font-bold">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <span>
      {renderText(displayed)}
      {!done && (
        <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-text-bottom" />
      )}
    </span>
  );
}

// ─── Render message content with markdown-lite ────────────────────────────────

function MessageContent({ content }: { content: string }) {
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={i} className="text-white font-bold">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

// ─── Progress sidebar ─────────────────────────────────────────────────────────

function ProgressSidebar({
  progress,
  industry,
}: {
  progress: Progress | null;
  industry: string | null;
}) {
  const knowledge = progress?.knowledge_score ?? 0;
  const overall = progress?.completion_percentage ?? 0;
  const deptProgress = progress?.progress ?? {};
  const currentDept = progress?.current_department;
  const missingInfo = progress?.missing_info ?? [];

  return (
    <div className="flex flex-col gap-4">
      {/* AI Brain card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
            <Brain className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <p className="text-xs font-bold text-white">OperationalBrain</p>
            <p className="text-[10px] text-slate-500">
              {industry ? `${industry} Mode` : "Learning Mode"}
            </p>
          </div>
        </div>

        {/* Knowledge score */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Knowledge Score
            </span>
            <span
              className={`text-xs font-bold ${
                knowledge >= 70
                  ? "text-emerald-400"
                  : knowledge >= 40
                  ? "text-amber-400"
                  : "text-orange-400"
              }`}
            >
              {knowledge}/100
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background:
                  knowledge >= 70
                    ? "linear-gradient(90deg, #6366f1, #22c55e)"
                    : knowledge >= 40
                    ? "linear-gradient(90deg, #6366f1, #eab308)"
                    : "linear-gradient(90deg, #6366f1, #f97316)",
              }}
              initial={{ width: 0 }}
              animate={{ width: `${knowledge}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Overall progress */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
              Interview Progress
            </span>
            <span className="text-xs font-bold text-indigo-300">{overall}%</span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-indigo-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${overall}%` }}
              transition={{ duration: 0.6 }}
            />
          </div>
        </div>
      </div>

      {/* Department progress */}
      {Object.keys(deptProgress).length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
            Departments
          </p>
          <div className="space-y-2.5">
            {Object.entries(deptProgress).map(([dept, pct]) => (
              <div key={dept}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`${
                        currentDept === dept
                          ? "text-indigo-400"
                          : pct === 100
                          ? "text-emerald-400"
                          : "text-slate-500"
                      }`}
                    >
                      {getDeptIcon(dept)}
                    </span>
                    <span
                      className={`text-[11px] font-medium ${
                        currentDept === dept
                          ? "text-indigo-300 font-bold"
                          : pct === 100
                          ? "text-emerald-400"
                          : "text-slate-400"
                      }`}
                    >
                      {dept}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {pct === 100 && (
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    )}
                    {currentDept === dept && pct < 100 && (
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-indigo-400"
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ duration: 1.2, repeat: Infinity }}
                      />
                    )}
                  </div>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${
                      pct === 100 ? "bg-emerald-500" : currentDept === dept ? "bg-indigo-500" : "bg-slate-700"
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing info */}
      {missingInfo.length > 0 && (
        <div className="bg-amber-950/30 border border-amber-500/20 rounded-2xl p-4">
          <p className="text-[10px] font-bold text-amber-400 uppercase tracking-widest mb-2 flex items-center gap-1">
            <Info className="w-3 h-3" /> To Cover
          </p>
          <ul className="space-y-1">
            {missingInfo.slice(0, 5).map((info, i) => (
              <li key={i} className="text-[10px] text-slate-400 flex items-start gap-1.5">
                <ChevronRight className="w-3 h-3 text-amber-500 flex-shrink-0 mt-0.5" />
                {info}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Stats */}
      {progress && (progress.questions_answered > 0 || progress.questions_asked > 0) && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] text-slate-500 mb-0.5">Questions</p>
            <p className="text-sm font-bold text-white">{progress.questions_answered}</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 mb-0.5">Answered</p>
            <p className="text-sm font-bold text-white">
              {progress.questions_answered}/{progress.questions_asked}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;
  const { workspaces, setActiveWorkspace } = useAuth();

  // View state
  const [viewState, setViewState] = useState<ViewState>("loading");

  // Session
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [detectedIndustry, setDetectedIndustry] = useState<string | null>(null);
  const [departmentQueue, setDepartmentQueue] = useState<string[]>([]);

  // Chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isAITyping, setIsAITyping] = useState(false);
  const [currentQuestionText, setCurrentQuestionText] = useState<string>("");
  const [currentDept, setCurrentDept] = useState<string>("General");
  const [currentCategory, setCurrentCategory] = useState<string>("general");
  const [isFirstQuestion, setIsFirstQuestion] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Progress
  const [progress, setProgress] = useState<Progress | null>(null);

  // Completion
  const [recommendations, setRecommendations] = useState<DeptRecommendation[]>([]);
  const [companyProfile, setCompanyProfile] = useState<any>(null);
  const [loadingRecs, setLoadingRecs] = useState(false);

  // Refs
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const lastAITypingRef = useRef(false);

  // Ensure workspace context
  useEffect(() => {
    const found = workspaces.find((w) => w.id === workspaceId);
    if (found) setActiveWorkspace(found);
  }, [workspaceId, workspaces, setActiveWorkspace]);

  useEffect(() => {
    setViewState("start");
  }, [workspaceId]);

  // Auto-scroll chat
  useEffect(() => {
    if (viewState === "chat") {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isAITyping, viewState]);

  // ── Add AI message with typing effect ──────────────────────────────────────
  const addAIMessage = useCallback(
    (content: string, dept?: string, cat?: string): Promise<void> => {
      return new Promise((resolve) => {
        const id = Date.now().toString();
        setIsAITyping(true);
        lastAITypingRef.current = true;

        // Show thinking indicator first
        const thinkingId = `thinking-${id}`;
        setMessages((prev) => [
          ...prev,
          { id: thinkingId, role: "ai", content: "", department: dept, category: cat, timestamp: new Date(), isTyping: true },
        ]);

        // After "thinking" delay, replace with typewriter
        const thinkDelay = Math.min(400 + content.length * 2, 1200);
        setTimeout(() => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === thinkingId ? { ...m, content, isTyping: false } : m
            )
          );
          setIsAITyping(false);
          lastAITypingRef.current = false;
          resolve();
        }, thinkDelay);
      });
    },
    []
  );

  // ── Start interview ──────────────────────────────────────────────────────
  const handleStart = async () => {
    setViewState("loading");
    setError(null);
    try {
      // 1. Start session
      const startRes = await api.post("/interview/start", { workspace_id: workspaceId });
      const sid = startRes.data.session_id;
      setSessionId(sid);
      setDetectedIndustry(startRes.data.detected_industry || null);
      setDepartmentQueue(startRes.data.department_queue || []);

      // 2. Set up initial progress shape
      const allDepts = ["General", ...(startRes.data.department_queue || [])];
      const initProgress: Progress = {
        progress: Object.fromEntries(allDepts.map((d) => [d, 0])),
        completion_percentage: 0,
        current_department: "General",
        knowledge_score: 0,
        department_confidence: {},
        missing_info: [],
        questions_asked: 0,
        questions_answered: 0,
      };
      setProgress(initProgress);

      setViewState("chat");
      setMessages([]);
      setIsFirstQuestion(true);

      // 3. Fetch first question
      await new Promise((r) => setTimeout(r, 300));
      const firstRes = await api.get(`/interview/first-question/${sid}`);
      const { ai_message, question_text, department, category } = firstRes.data;

      setCurrentQuestionText(question_text || "");
      setCurrentDept(department || "General");
      setCurrentCategory(category || "general");
      setIsFirstQuestion(false);

      await addAIMessage(ai_message, department, category);

      // Focus input
      setTimeout(() => inputRef.current?.focus(), 200);
    } catch (err) {
      setError(formatError(err, "Failed to start interview."));
      setViewState("start");
    }
  };

  // ── Submit user answer ───────────────────────────────────────────────────
  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      const msg = inputValue.trim();
      if (!msg || !sessionId || submitting || isAITyping) return;

      setSubmitting(true);
      setError(null);
      setInputValue("");

      // Add user message
      const userMsgId = Date.now().toString();
      setMessages((prev) => [
        ...prev,
        {
          id: userMsgId,
          role: "user",
          content: msg,
          timestamp: new Date(),
        },
      ]);

      try {
        const res = await api.post("/interview/chat", {
          session_id: sessionId,
          message: msg,
        });

        const {
          ai_message,
          question_text,
          department,
          category,
          is_followup,
          session_complete,
          progress: progressData,
        } = res.data;

        // Update progress
        if (progressData) {
          setProgress(progressData);
        }

        if (session_complete) {
          // Show completion message first
          await addAIMessage(ai_message, department, category);
          setViewState("completing");

          // Brief delay then show completed state
          setTimeout(() => {
            setViewState("completed");
            // Load data
            loadCompletionData();
          }, 2000);
          return;
        }

        // Update current question context
        if (!is_followup) {
          setCurrentQuestionText(question_text || "");
          setCurrentDept(department || currentDept);
          setCurrentCategory(category || currentCategory);
        }

        await addAIMessage(ai_message, department, category);
        setTimeout(() => inputRef.current?.focus(), 100);
      } catch (err) {
        setError(formatError(err, "Failed to send message."));
        setSubmitting(false);
        return;
      }

      setSubmitting(false);
    },
    [inputValue, sessionId, submitting, isAITyping, currentDept, currentCategory, addAIMessage]
  );

  // ── Keyboard handler ─────────────────────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // ── Load completion data ─────────────────────────────────────────────────
  const loadCompletionData = async () => {
    if (!sessionId) return;
    setLoadingRecs(true);
    try {
      const [recsRes, profileRes, progressRes] = await Promise.all([
        api.get(`/interview/recommendations/${sessionId}`).catch(() => null),
        api.get(`/interview/company-profile/${workspaceId}`).catch(() => null),
        api.get(`/interview/progress/${sessionId}`).catch(() => null),
      ]);

      if (recsRes?.data?.recommendations) {
        setRecommendations(recsRes.data.recommendations);
      }
      if (profileRes?.data) {
        setCompanyProfile(profileRes.data);
      }
      if (progressRes?.data) {
        setProgress(progressRes.data);
      }
    } catch (err) {
      console.error("Failed to load completion data", err);
    } finally {
      setLoadingRecs(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Loading
  // ─────────────────────────────────────────────────────────────────────────
  if (viewState === "loading") {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
              <Brain className="w-8 h-8 text-indigo-400" />
            </div>
            <div className="absolute inset-0 rounded-2xl border-2 border-indigo-500/40 animate-ping" />
          </div>
          <p className="text-slate-400 text-sm">Initializing Interview Engine...</p>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Start screen
  // ─────────────────────────────────────────────────────────────────────────
  if (viewState === "start") {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="w-full max-w-2xl"
        >
          {/* Hero card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl overflow-hidden backdrop-blur-md">
            {/* Gradient banner */}
            <div className="h-2 bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500" />

            <div className="p-10 text-center">
              {/* AI Avatar */}
              <div className="relative inline-flex mb-6">
                <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-2xl shadow-indigo-900/40">
                  <Brain className="w-12 h-12 text-white" />
                </div>
                <motion.div
                  className="absolute inset-0 rounded-3xl border-2 border-indigo-400/40"
                  animate={{ scale: [1, 1.12, 1] }}
                  transition={{ duration: 2.5, repeat: Infinity }}
                />
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-slate-900 flex items-center justify-center">
                  <Zap className="w-3 h-3 text-white" />
                </div>
              </div>

              <h1 className="text-3xl font-extrabold text-white mb-3 tracking-tight">
                Company Intelligence Interview
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto mb-8">
                I'm your OperationalBrain AI. I'll interview you exactly like a newly hired employee — asking
                smart, industry-specific questions to deeply understand your organization.
              </p>

              {/* Feature pills */}
              <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
                {[
                  { icon: <Sparkles className="w-3.5 h-3.5" />, label: "AI-Driven Questions" },
                  { icon: <TrendingUp className="w-3.5 h-3.5" />, label: "Live Progress Tracking" },
                  { icon: <FileText className="w-3.5 h-3.5" />, label: "Company Profile Generated" },
                  { icon: <BookOpen className="w-3.5 h-3.5" />, label: "Document Recommendations" },
                ].map((f, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/10 border border-indigo-600/20 text-indigo-300 rounded-full text-[11px] font-semibold"
                  >
                    {f.icon} {f.label}
                  </span>
                ))}
              </div>

              {/* What to expect */}
              <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-5 mb-8 text-left grid grid-cols-2 gap-4">
                {[
                  { step: "01", title: "General Overview", desc: "Business, locations, ERP, headcount" },
                  { step: "02", title: "Department Deep-Dive", desc: "Industry-specific questions per dept" },
                  { step: "03", title: "Intelligent Follow-ups", desc: "AI asks smarter based on your answers" },
                  { step: "04", title: "Profile & Recommendations", desc: "Company profile + document checklist" },
                ].map((item) => (
                  <div key={item.step} className="flex gap-3">
                    <span className="text-[10px] font-black text-indigo-400 bg-indigo-600/10 w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0">
                      {item.step}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-white">{item.title}</p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              <button
                id="start-interview-btn"
                onClick={handleStart}
                className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl transition-all shadow-[0_0_30px_rgba(79,70,229,0.4)] hover:shadow-[0_0_40px_rgba(79,70,229,0.6)] hover:scale-105 active:scale-100 text-sm"
              >
                <Brain className="w-5 h-5" />
                Begin Interview
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Completing (transition state)
  // ─────────────────────────────────────────────────────────────────────────
  if (viewState === "completing") {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <div className="relative inline-flex">
            <div className="w-20 h-20 rounded-3xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
              <Brain className="w-10 h-10 text-indigo-400" />
            </div>
            <div className="absolute inset-0 rounded-3xl border-2 border-indigo-400/40 animate-ping" />
          </div>
          <p className="text-white font-bold text-lg">Generating your Company Profile...</p>
          <p className="text-slate-400 text-sm">Building document recommendations</p>
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin mx-auto" />
        </motion.div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Completed + Recommendations
  // ─────────────────────────────────────────────────────────────────────────
  if (viewState === "completed" || viewState === "recommendations") {
    const ks = progress?.knowledge_score ?? companyProfile?.ai_readiness_score ?? 0;

    return (
      <div className="p-6 max-w-6xl mx-auto">
        <AnimatePresence mode="wait">
          {viewState === "completed" && (
            <motion.div
              key="completed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Success banner */}
              <div className="bg-gradient-to-r from-emerald-900/40 to-indigo-900/40 border border-emerald-500/30 rounded-2xl p-6 flex items-center gap-5">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
                <div className="flex-1">
                  <h1 className="text-2xl font-extrabold text-white mb-1">Interview Complete!</h1>
                  <p className="text-slate-400 text-sm">
                    OperationalBrain has captured your company's knowledge. Your profile and document
                    recommendations are ready.
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Knowledge Score</p>
                  <p className="text-3xl font-black text-emerald-400">{ks}</p>
                  <p className="text-[10px] text-slate-500">out of 100</p>
                </div>
              </div>

              {/* Company profile card */}
              {companyProfile && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-indigo-400" />
                    Company Profile Generated
                  </h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: "Industry", value: companyProfile.industry || "—" },
                      { label: "Employees", value: companyProfile.employee_count || "—" },
                      { label: "ERP System", value: companyProfile.erp || "—" },
                      { label: "AI Readiness", value: `${companyProfile.ai_readiness_score ?? ks}%` },
                    ].map((item) => (
                      <div key={item.label} className="bg-slate-800/50 border border-slate-700/40 rounded-xl p-3">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{item.label}</p>
                        <p className="text-sm font-bold text-white truncate">{item.value}</p>
                      </div>
                    ))}
                  </div>

                  {companyProfile.products?.length > 0 && (
                    <div className="mt-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Products Identified</p>
                      <div className="flex flex-wrap gap-2">
                        {companyProfile.products.map((p: string, i: number) => (
                          <span key={i} className="px-2.5 py-1 bg-indigo-600/10 border border-indigo-600/20 text-indigo-300 rounded-lg text-xs">
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {companyProfile.departments?.length > 0 && (
                    <div className="mt-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Departments Covered</p>
                      <div className="flex flex-wrap gap-2">
                        {companyProfile.departments.map((d: string, i: number) => (
                          <span key={i} className="px-2.5 py-1 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1">
                            {getDeptIcon(d)} {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Recommendations preview */}
              {loadingRecs ? (
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" /> Loading recommendations...
                </div>
              ) : recommendations.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      Recommended Documents
                    </h2>
                    <span className="text-[10px] text-slate-500">
                      {recommendations.reduce((s, r) => s + r.documents.length, 0)} documents across{" "}
                      {recommendations.length} departments
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendations.map((dept, di) => (
                      <motion.div
                        key={dept.department}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: di * 0.06 }}
                        className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4"
                      >
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-indigo-400">{getDeptIcon(dept.department)}</span>
                          <h3 className="text-xs font-bold text-white">{dept.department}</h3>
                          <span className="ml-auto text-[10px] text-slate-500">
                            {dept.documents.length} docs
                          </span>
                        </div>
                        <div className="space-y-2">
                          {dept.documents.map((doc, doci) => {
                            const colors = PRIORITY_COLORS[doc.priority] ?? PRIORITY_COLORS.medium;
                            return (
                              <div
                                key={doci}
                                className={`flex items-start gap-2.5 p-2.5 rounded-xl border ${colors.bg} ${colors.border}`}
                              >
                                <FileText className={`w-3.5 h-3.5 ${colors.text} flex-shrink-0 mt-0.5`} />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5 flex-wrap">
                                    <p className="text-[11px] font-semibold text-white leading-tight">
                                      {doc.document_name}
                                    </p>
                                    <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}>
                                      {doc.priority}
                                    </span>
                                  </div>
                                  <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">
                                    {doc.reason}
                                  </p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => router.push(`/workspaces/${workspaceId}`)}
                  className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-sm transition-colors"
                >
                  Return to Workspace
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Chat UI
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Chat header */}
        <div className="border-b border-slate-900 px-6 py-3 flex items-center gap-3 bg-slate-950/40 backdrop-blur-sm flex-shrink-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">OperationalBrain</p>
            <p className="text-[10px] text-emerald-400 flex items-center gap-1">
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              {isAITyping ? "Thinking..." : "Active · Company Interview Mode"}
            </p>
          </div>
          {detectedIndustry && (
            <span className="ml-auto px-2.5 py-1 bg-indigo-600/10 border border-indigo-600/20 text-indigo-300 rounded-lg text-[10px] font-semibold">
              {detectedIndustry}
            </span>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                {/* Avatar */}
                {msg.role === "ai" && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <Brain className="w-4 h-4 text-white" />
                  </div>
                )}
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-slate-700 border border-slate-600 flex items-center justify-center flex-shrink-0 mt-1 text-xs font-bold text-white">
                    U
                  </div>
                )}

                {/* Bubble */}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "ai"
                      ? "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm"
                      : "bg-indigo-600 text-white rounded-tr-sm"
                  }`}
                >
                  {msg.isTyping ? (
                    <TypingIndicator />
                  ) : msg.role === "ai" && messages[messages.length - 1]?.id === msg.id && !isAITyping ? (
                    <TypewriterText key={msg.id} text={msg.content} />
                  ) : (
                    <MessageContent content={msg.content} />
                  )}

                  {/* Department badge */}
                  {msg.role === "ai" && !msg.isTyping && msg.department && msg.department !== "General" && (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <span className="inline-flex items-center gap-1 text-[10px] text-slate-500">
                        {getDeptIcon(msg.department)}
                        <span>{msg.department}</span>
                        {msg.category && <span className="text-slate-600">· {msg.category}</span>}
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="px-6 pb-2">
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-slate-900 px-6 py-4 bg-slate-950/40 backdrop-blur-sm flex-shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <textarea
              id="interview-input"
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isAITyping ? "AI is thinking..." : "Type your answer… (Enter to send)"}
              disabled={isAITyping || submitting}
              rows={1}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors resize-none min-h-[48px] max-h-32 disabled:opacity-60"
              style={{ height: "auto" }}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = "auto";
                el.style.height = Math.min(el.scrollHeight, 128) + "px";
              }}
            />
            <button
              id="interview-send-btn"
              type="submit"
              disabled={!inputValue.trim() || isAITyping || submitting}
              className="w-12 h-12 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:scale-105 active:scale-95 flex-shrink-0 shadow-lg shadow-indigo-900/30"
            >
              {submitting ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          <p className="text-[10px] text-slate-600 mt-2 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Right sidebar */}
      <div className="w-72 border-l border-slate-900 overflow-y-auto p-4 flex-shrink-0 hidden lg:block bg-slate-950/20">
        <ProgressSidebar progress={progress} industry={detectedIndustry} />
      </div>
    </div>
  );
}
