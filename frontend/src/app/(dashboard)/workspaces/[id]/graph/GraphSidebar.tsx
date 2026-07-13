import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Network, Activity, AlertTriangle, MapPin, FileText, Wrench, ShieldCheck, ClipboardList, Info, Box } from "lucide-react";
import { NodeDetails } from "./types";

interface GraphSidebarProps {
  selectedNode: any;
  entityDetails: NodeDetails | null;
  loadingDetails: boolean;
}

export default function GraphSidebar({ selectedNode, entityDetails, loadingDetails }: GraphSidebarProps) {
  return (
    <div className="w-[25%] shrink-0 h-full">
      <AnimatePresence mode="wait">
        {selectedNode ? (
          <motion.div
            key="panel"
            initial={{ opacity: 0, x: -20, width: 0 }}
            animate={{ opacity: 1, x: 0, width: "100%" }}
            exit={{ opacity: 0, x: -20, width: 0 }}
            className="flex flex-col gap-4 overflow-hidden h-full w-full"
          >
            <div className="glass-card flex-1 p-5 rounded-xl flex flex-col gap-5 overflow-y-auto w-full custom-scrollbar">
              <NodeInspector node={selectedNode} details={entityDetails} loading={loadingDetails} />
              {!loadingDetails && <CopilotAI node={selectedNode} details={entityDetails} />}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card flex-1 p-5 rounded-xl h-full flex flex-col items-center justify-center text-slate-500 gap-4"
          >
            <Network className="w-12 h-12 text-slate-700/50" />
            <p className="text-sm text-center">Select a node to inspect.</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Subcomponents
function NodeInspector({ node, details, loading }: { node: any; details: NodeDetails | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <>
      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">
          Asset Information
        </span>
        <h2 className="text-xl font-bold text-white truncate" title={node.label}>
          {node.label}
        </h2>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20 uppercase">
            {node.type}
          </span>
        </div>
      </div>

      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-3 border-b border-slate-800 pb-1">
          Knowledge Summary
        </span>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center gap-1"><Activity className="w-3 h-3"/> Health</div>
            <div className="text-emerald-400 font-bold text-lg">{node.properties?.health || "N/A"}</div>
          </div>
          <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Risk</div>
            <div className="text-amber-400 font-bold text-lg">{node.properties?.risk || "N/A"}</div>
          </div>
          <div className="col-span-2 bg-slate-900/40 p-3 rounded-xl border border-slate-800 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-indigo-400" />
            <div>
              <div className="text-slate-400 text-[10px]">Area</div>
              <div className="text-white font-semibold">{node.properties?.area || "Unknown"}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 bg-blue-500/10 text-blue-400 px-2.5 py-1.5 rounded-lg border border-blue-500/20 text-xs font-semibold flex-1 justify-center">
          <FileText className="w-3.5 h-3.5" />
          {details?.docsCount || 0} Docs
        </div>
        <div className="flex items-center gap-1.5 bg-purple-500/10 text-purple-400 px-2.5 py-1.5 rounded-lg border border-purple-500/20 text-xs font-semibold flex-1 justify-center">
          <Wrench className="w-3.5 h-3.5" />
          {details?.maintCount || 0} Maint
        </div>
        <div className="flex items-center gap-1.5 bg-orange-500/10 text-orange-400 px-2.5 py-1.5 rounded-lg border border-orange-500/20 text-xs font-semibold flex-1 justify-center">
          <ShieldCheck className="w-3.5 h-3.5" />
          {details?.inspCount || 0} Insp
        </div>
        <div className="flex items-center gap-1.5 bg-teal-500/10 text-teal-400 px-2.5 py-1.5 rounded-lg border border-teal-500/20 text-xs font-semibold flex-1 justify-center">
          <ClipboardList className="w-3.5 h-3.5" />
          {details?.woCount || 0} WOs
        </div>
      </div>

      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2 border-b border-slate-800 pb-1">
          Connected Equipment
        </span>
        <div className="space-y-2">
          {details?.relatedAssets?.length ? (
            details.relatedAssets.map((asset, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs bg-slate-900/30 p-2 rounded-lg border border-slate-800/50 hover:bg-slate-800/50 cursor-pointer transition-colors">
                <Box className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-slate-300 font-medium">{asset.label}</span>
                <span className="ml-auto text-[9px] text-slate-500 uppercase">{asset.type}</span>
              </div>
            ))
          ) : (
            <span className="text-xs text-slate-500 italic">No related equipment found.</span>
          )}
        </div>
      </div>
    </>
  );
}

function CopilotAI({ node, details }: { node: any; details: NodeDetails | null }) {
  if (!details) return null;

  return (
    <>
      <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/5 border border-indigo-500/20 p-4 rounded-xl mt-4">
        <div className="flex items-center gap-2 mb-2">
          <Info className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-indigo-300 uppercase tracking-widest">AI Summary</span>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">
          {details.aiSummary || `${node.label} is operating normally.`}
        </p>
      </div>

      <div className="mt-2">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-3 border-b border-slate-800 pb-1">
          Recommended Actions
        </span>
        <ul className="space-y-2">
          {details.recommendations?.length ? (
            details.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-300 bg-slate-900/40 p-3 rounded-xl border border-slate-800">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                <span>{rec}</span>
              </li>
            ))
          ) : (
            <li className="text-xs text-slate-500 italic">No recommendations.</li>
          )}
        </ul>
      </div>
    </>
  );
}
