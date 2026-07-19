"use client";

import React, { useState, useEffect } from "react";
import { api } from "../../../../lib/api";
import { 
  Loader2, Activity, ShieldAlert, CheckCircle2, AlertTriangle, 
  Settings, Clock, FileText, Wrench, Search, Box, ChevronDown, ChevronUp, Info, ChevronRight, Zap
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Equipment {
  name: string;
  type: string;
}

interface MaintenanceIntelligence {
  equipment: string;
  equipment_type: string;
  location: string;
  manufacturer: string;
  operational_status: string;
  health_score: number;
  risk_level: string;
  confidence: number;
  confidence_reason: string;
  kpis: {
    mtbf: string;
    mttr: string;
    inspection_compliance: string;
    maintenance_readiness: string;
  };
  predicted_failure: Array<{ risk: string; probability_percent: number }>;
  possible_causes: string[];
  inspection_checklist: Array<{ task: string; checked: boolean }>;
  recommended_actions: Array<{ action: string; priority: string }>;
  spare_parts: Array<{ part: string; quantity: number; oem_recommendation: string }>;
  timeline: Array<{ timeframe: string; task: string }>;
  maintenance_history: Array<{ date: string; event: string }>;
  safety_precautions: string[];
  compliance: Array<{ standard: string; met: boolean }>;
  next_maintenance: string;
  ai_insights: {
    observation: string;
    likely_cause: string;
    recommendation: string;
  };
  evidence: Array<{ document: string; page: string | number; type: string; similarity: number }>;
  similar_incidents: Array<{ equipment: string; issue: string; similarity: string }>;
}

const CircularGauge = ({ value, title }: { value: number; title: string }) => {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  
  let color = "text-emerald-500";
  if (value < 50) color = "text-red-500";
  else if (value < 80) color = "text-amber-500";
  
  return (
    <div className="flex flex-col items-center justify-center bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
      <div className="relative w-28 h-28 flex items-center justify-center">
        <svg className="transform -rotate-90 w-28 h-28">
          <circle cx="56" cy="56" r="36" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-800" />
          <circle cx="56" cy="56" r="36" stroke="currentColor" strokeWidth="8" fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={`${color} transition-all duration-1000 ease-out`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-3xl font-black text-white">{value}</span>
        </div>
      </div>
      <span className="text-xs font-bold text-slate-400 mt-4 uppercase tracking-widest">{title}</span>
    </div>
  );
};

export default function MaintenanceTab({ workspaceId }: { workspaceId: string }) {
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [filteredEquipment, setFilteredEquipment] = useState<Equipment[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingEquip, setLoadingEquip] = useState(true);
  
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [intelligence, setIntelligence] = useState<MaintenanceIntelligence | null>(null);
  const [loadingIntell, setLoadingIntell] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [expandedEvidence, setExpandedEvidence] = useState(false);

  useEffect(() => {
    const fetchEquipment = async () => {
      try {
        setLoadingEquip(true);
        const res = await api.get(`/maintenance/equipment?workspace_id=${workspaceId}`);
        setEquipmentList(res.data);
        setFilteredEquipment(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingEquip(false);
      }
    };
    fetchEquipment();
  }, [workspaceId]);

  useEffect(() => {
    const lower = searchQuery.toLowerCase();
    setFilteredEquipment(equipmentList.filter(e => e.name.toLowerCase().includes(lower)));
  }, [searchQuery, equipmentList]);

  const loadIntelligence = async (equipName: string) => {
    setSelectedEquipment(equipName);
    setIntelligence(null);
    setError(null);
    setLoadingIntell(true);
    
    try {
      const res = await api.get(`/maintenance/intelligence?workspace_id=${workspaceId}&equipment_name=${encodeURIComponent(equipName)}`);
      setIntelligence(res.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to load intelligence.");
    } finally {
      setLoadingIntell(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    const p = priority.toLowerCase();
    if (p.includes("immediate")) return "bg-red-500/10 text-red-500 border-red-500/20";
    if (p.includes("today")) return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    if (p.includes("preventive")) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
  };

  return (
    <div className="flex h-[calc(100vh-140px)] animate-in fade-in duration-300 gap-6">
      
      {/* Left Panel - Equipment Selector */}
      <div className="w-80 flex flex-col gap-4">
        <div className="glass-card p-4 flex flex-col h-full border border-slate-800">
          <h2 className="text-sm font-black text-white mb-4 uppercase tracking-widest flex items-center gap-2">
            <Settings className="w-4 h-4 text-indigo-400" /> Equipment Matrix
          </h2>
          
          <div className="relative mb-4">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search assets..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
            {loadingEquip ? (
              <div className="flex items-center justify-center h-24 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : filteredEquipment.length === 0 ? (
              <div className="text-center p-4 text-slate-500 text-xs">No equipment found in knowledge base.</div>
            ) : (
              filteredEquipment.map((eq, i) => (
                <button
                  key={i}
                  onClick={() => loadIntelligence(eq.name)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selectedEquipment === eq.name 
                      ? "bg-indigo-600/10 border-indigo-500/50 text-indigo-400" 
                      : "bg-slate-900/50 border-slate-800/50 text-slate-300 hover:bg-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="font-bold text-sm truncate">{eq.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-1">{eq.type.toUpperCase()}</div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {!selectedEquipment ? (
          <div className="flex-1 flex flex-col items-center justify-center glass-card border border-slate-800 text-slate-400">
            <Activity className="w-16 h-16 text-slate-600 mb-6" />
            <h2 className="text-xl font-black text-white mb-2">Enterprise Maintenance AI</h2>
            <p className="text-sm text-center max-w-md">Select an equipment from the matrix to generate a deterministic, evidence-backed maintenance report.</p>
          </div>
        ) : loadingIntell ? (
          <div className="flex-1 flex flex-col items-center justify-center glass-card border border-slate-800">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-500/20 blur-xl rounded-full" />
              <Loader2 className="w-12 h-12 animate-spin text-indigo-400 relative z-10" />
            </div>
            <h3 className="text-lg font-bold text-white mt-8 mb-2">Analyzing Knowledge Graph...</h3>
            <p className="text-xs text-slate-400 max-w-sm text-center">Reading manuals, inspection reports, and maintenance history for {selectedEquipment}.</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center glass-card border border-red-900/30 text-red-400">
            <AlertTriangle className="w-12 h-12 mb-4 text-red-500" />
            <p>{error}</p>
          </div>
        ) : intelligence ? (
          <motion.div 
            className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10 space-y-6"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.15 }
              }
            }}
          >
            
            {/* Header Row */}
            <div className="flex gap-6 items-stretch">
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800 flex-1 flex flex-col justify-center relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                  <Settings className="w-48 h-48" />
                </div>
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="px-3 py-1 bg-indigo-500/20 text-indigo-400 rounded text-[10px] font-black tracking-widest uppercase border border-indigo-500/30">
                      {intelligence.equipment_type}
                    </span>
                    <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded text-[10px] font-black tracking-widest uppercase border border-slate-700">
                      {intelligence.manufacturer}
                    </span>
                  </div>
                  <h1 className="text-4xl font-black text-white mb-1">{intelligence.equipment}</h1>
                  <p className="text-sm text-slate-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                    {intelligence.operational_status} • {intelligence.location}
                  </p>
                </div>
              </motion.div>
              
              <motion.div variants={{ hidden: { opacity: 0, scale: 0.8 }, visible: { opacity: 1, scale: 1, transition: { type: "spring" } } }}>
                <CircularGauge value={intelligence.health_score} title="Health Score" />
              </motion.div>
            </div>

            {/* AI Insights & Risk */}
            <div className="grid grid-cols-3 gap-6">
              
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="col-span-2 glass-card p-6 border border-indigo-500/30 bg-gradient-to-br from-indigo-900/20 to-slate-900/50 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
                <h3 className="text-xs font-black text-indigo-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                  <Zap className="w-4 h-4" /> AI Diagnostics
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Observation</span>
                    <p className="text-sm text-slate-200 font-medium leading-relaxed">{intelligence.ai_insights.observation}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Root Cause Analysis</span>
                    <p className="text-sm text-amber-400/90 font-medium">{intelligence.ai_insights.likely_cause}</p>
                  </div>
                  <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                    <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block mb-1">Recommended Strategy</span>
                    <p className="text-sm text-indigo-100 font-bold">{intelligence.ai_insights.recommendation}</p>
                  </div>
                </div>
              </motion.div>

              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800 flex flex-col">
                <h3 className="text-xs font-black text-slate-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-red-400" /> Failure Risks
                </h3>
                <div className="flex-1 space-y-5">
                  {intelligence.predicted_failure.length > 0 ? intelligence.predicted_failure.map((f, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-xs font-bold mb-2">
                        <span className="text-slate-200">{f.risk}</span>
                        <span className={f.probability_percent > 70 ? "text-red-400" : f.probability_percent > 40 ? "text-amber-400" : "text-emerald-400"}>
                          {f.probability_percent}%
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${f.probability_percent > 70 ? "bg-red-500" : f.probability_percent > 40 ? "bg-amber-500" : "bg-emerald-500"} transition-all duration-1000`}
                          style={{ width: `${f.probability_percent}%` }}
                        />
                      </div>
                    </div>
                  )) : (
                    <p className="text-xs text-slate-500 italic">No significant failure risks detected.</p>
                  )}
                </div>
              </motion.div>
            </div>

            {/* KPIs & Compliance */}
            <motion.div variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }} className="grid grid-cols-4 gap-4">
              {[
                { label: "MTBF", value: intelligence.kpis.mtbf },
                { label: "Est. MTTR", value: intelligence.kpis.mttr },
                { label: "Inspection Compliance", value: intelligence.kpis.inspection_compliance },
                { label: "Maintenance Readiness", value: intelligence.kpis.maintenance_readiness }
              ].map((kpi, i) => (
                <motion.div key={i} variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }} className="glass-card p-5 border border-slate-800 flex flex-col items-center justify-center text-center">
                  <span className="text-2xl font-black text-white mb-1">{kpi.value}</span>
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{kpi.label}</span>
                </motion.div>
              ))}
            </motion.div>

            <div className="grid grid-cols-2 gap-6">
              {/* Actions */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800">
                <h3 className="text-xs font-black text-slate-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-indigo-400" /> Prescriptive Actions
                </h3>
                <div className="space-y-3">
                  {intelligence.recommended_actions.length > 0 ? intelligence.recommended_actions.map((act, i) => (
                    <div key={i} className={`p-4 rounded-xl border flex gap-4 ${getPriorityColor(act.priority)}`}>
                      <div className="flex-1">
                        <div className="text-[10px] font-black uppercase tracking-widest mb-1 opacity-80">{act.priority}</div>
                        <p className="text-sm font-semibold">{act.action}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 opacity-50 my-auto" />
                    </div>
                  )) : (
                     <p className="text-xs text-slate-500 italic">No recommended actions.</p>
                  )}
                </div>
              </motion.div>

              {/* Checklist & Compliance */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800 flex flex-col">
                <h3 className="text-xs font-black text-slate-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Compliance & Inspection
                </h3>
                
                <div className="mb-6 flex flex-wrap gap-2">
                  {intelligence.compliance.length > 0 ? intelligence.compliance.map((c, i) => (
                    <span key={i} className={`px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 ${c.met ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
                      {c.met ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                      {c.standard}
                    </span>
                  )) : (
                    <span className="text-xs text-slate-500 italic">No compliance standards found.</span>
                  )}
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto custom-scrollbar pr-2 max-h-[300px]">
                  {intelligence.inspection_checklist.length > 0 ? intelligence.inspection_checklist.map((chk, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-slate-900/50 rounded-xl border border-slate-800/50">
                      <div className={`mt-0.5 shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center ${chk.checked ? "border-emerald-500 bg-emerald-500" : "border-slate-600"}`}>
                        {chk.checked && <CheckCircle2 className="w-3 h-3 text-white" />}
                      </div>
                      <span className={`text-sm ${chk.checked ? "text-slate-400 line-through" : "text-slate-200 font-medium"}`}>{chk.task}</span>
                    </div>
                  )) : (
                    <p className="text-xs text-slate-500 italic">No inspection checklist found.</p>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Timeline & Parts */}
            <div className="grid grid-cols-2 gap-6">
              
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800">
                <h3 className="text-xs font-black text-slate-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-400" /> Maintenance Timeline
                </h3>
                <div className="relative border-l-2 border-slate-800 ml-3 pl-6 space-y-8">
                  {intelligence.timeline.length > 0 ? intelligence.timeline.map((t, i) => (
                    <div key={i} className="relative">
                      <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[31px] top-1.5 shadow-[0_0_10px_rgba(99,102,241,0.8)]" />
                      <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{t.timeframe}</div>
                      <p className="text-sm text-slate-200 font-medium">{t.task}</p>
                    </div>
                  )) : (
                     <p className="text-xs text-slate-500 italic">No timeline available.</p>
                  )}
                </div>
              </motion.div>

              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card p-6 border border-slate-800">
                <h3 className="text-xs font-black text-slate-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                  <Box className="w-4 h-4 text-indigo-400" /> Required Spare Parts
                </h3>
                {intelligence.spare_parts.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-500 text-[10px] uppercase tracking-widest font-bold">
                          <th className="pb-3">Part</th>
                          <th className="pb-3 text-center">Qty</th>
                          <th className="pb-3">OEM Rec.</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/50">
                        {intelligence.spare_parts.map((p, i) => (
                          <tr key={i}>
                            <td className="py-3 font-medium text-slate-200">{p.part}</td>
                            <td className="py-3 text-center text-slate-400 font-mono">{p.quantity}</td>
                            <td className="py-3 text-slate-400 text-xs">{p.oem_recommendation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No spare parts identified.</p>
                )}
              </motion.div>
            </div>

            {/* Evidence Accordion */}
            <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring" } } }} className="glass-card border border-slate-800 overflow-hidden">
              <button 
                onClick={() => setExpandedEvidence(!expandedEvidence)}
                className="w-full p-6 flex justify-between items-center bg-slate-900/50 hover:bg-slate-800/50 transition-colors"
              >
                <div>
                  <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-400" /> Grounding Evidence
                  </h3>
                  <p className="text-xs text-slate-500 mt-2 text-left font-mono">{intelligence.confidence_reason}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="block text-2xl font-black text-emerald-400">{intelligence.confidence}%</span>
                    <span className="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Confidence</span>
                  </div>
                  {expandedEvidence ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
                </div>
              </button>
              
              <AnimatePresence>
                {expandedEvidence && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-slate-800 bg-slate-950 p-6"
                  >
                    <div className="grid grid-cols-2 gap-4">
                      {intelligence.evidence.map((ev, i) => (
                        <div key={i} className="p-4 rounded-xl bg-slate-900 border border-slate-800/80 hover:border-emerald-500/30 transition-colors">
                          <div className="flex justify-between items-start mb-2">
                            <span className="px-2 py-1 bg-slate-800 text-slate-300 text-[9px] font-black uppercase tracking-widest rounded border border-slate-700">
                              {ev.type}
                            </span>
                            <span className="text-emerald-400 text-xs font-black font-mono">{(ev.similarity * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-sm font-bold text-slate-200 mb-1 truncate">{ev.document}</p>
                          <p className="text-xs text-slate-500 font-mono">Page {ev.page}</p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
            
            <div className="h-8" />
          </motion.div>
        ) : null}
      </div>
    </div>
  );
}
