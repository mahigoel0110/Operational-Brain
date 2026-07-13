import React from "react";
import { Search, Filter, Layout, Calendar, BarChart2, CheckSquare, Square, ChevronDown } from "lucide-react";
import { GraphData } from "./types";

interface GraphRightPanelProps {
  data: GraphData;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onSearchSelect: (id: string) => void;
  layoutName: string;
  setLayoutName: (name: string) => void;
  timeline: string;
  setTimeline: (t: string) => void;
  filters: Record<string, boolean>;
  toggleFilter: (type: string) => void;
}

export default function GraphRightPanel({
  data,
  searchQuery,
  setSearchQuery,
  onSearchSelect,
  layoutName,
  setLayoutName,
  timeline,
  setTimeline,
  filters,
  toggleFilter
}: GraphRightPanelProps) {

  // Auto-suggestions logic
  const suggestions = searchQuery.trim()
    ? data.nodes.filter(n => n.label.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 5)
    : [];

  const layoutOptions = ["cose", "circle", "grid", "concentric", "breadthfirst"];
  const timelineOptions = ["Today", "Last Week", "Last Month", "All Time"];

  // Stats
  const visibleNodes = data.nodes.filter(n => filters[n.type] !== false);
  const equipmentNodes = visibleNodes.filter(n => ['Equipment', 'Pump', 'Valve', 'Tank', 'Motor', 'Boiler', 'Compressor', 'Heat Exchanger'].includes(n.type)).length;
  const documentNodes = visibleNodes.filter(n => ['Document', 'Manual', 'SOP'].includes(n.type)).length;
  
  // This is a naive edge count since actual visible edges depend on cytoscape graph state, but this is for UI stats
  const totalEdges = data.edges.length;
  const avgDegree = visibleNodes.length > 0 ? ((totalEdges * 2) / visibleNodes.length).toFixed(1) : "0";

  return (
    <div className="w-[25%] flex flex-col gap-4 overflow-y-auto custom-scrollbar shrink-0 h-full relative z-30">
      
      {/* Search Autocomplete */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3 relative">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Search className="w-4 h-4 text-indigo-400" />
          Search Assets
        </h3>
        <div className="relative">
          <input
            type="text"
            placeholder="Search (e.g. Pump)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-700/50 rounded-lg pl-3 pr-8 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden z-50 shadow-2xl">
              {suggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    onSearchSelect(s.id);
                    setSearchQuery("");
                  }}
                  className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors truncate flex items-center gap-2"
                >
                  <span className="font-semibold text-indigo-300 uppercase text-[9px] min-w-[50px]">{s.type}</span>
                  <span className="truncate">{s.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Graph Settings */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Layout className="w-4 h-4 text-indigo-400" />
          Layout
        </h3>
        <div className="relative">
          <select
            value={layoutName}
            onChange={(e) => setLayoutName(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-700/50 rounded-lg pl-3 pr-8 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 appearance-none capitalize"
          >
            {layoutOptions.map((opt) => (
              <option key={opt} value={opt} className="bg-slate-800">{opt === 'cose' ? 'Force Directed' : opt}</option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-2.5 pointer-events-none" />
        </div>
      </div>

      {/* Toggles */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Filter className="w-4 h-4 text-indigo-400" />
          Node Types
        </h3>
        <div className="flex flex-col gap-2">
          {Object.entries(filters).map(([type, isActive]) => (
            <button
              key={type}
              onClick={() => toggleFilter(type)}
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
            >
              {isActive ? (
                <CheckSquare className="w-4 h-4 text-indigo-400" />
              ) : (
                <Square className="w-4 h-4 text-slate-600" />
              )}
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3 mt-auto">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-indigo-400" />
          Graph Statistics
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Equipment</span>
            <span className="font-bold text-white text-sm">{equipmentNodes}</span>
          </div>
          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Documents</span>
            <span className="font-bold text-white text-sm">{documentNodes}</span>
          </div>
          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Total Edges</span>
            <span className="font-bold text-white text-sm">{totalEdges}</span>
          </div>
          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Avg Degree</span>
            <span className="font-bold text-white text-sm">{avgDegree}</span>
          </div>
        </div>
      </div>

    </div>
  );
}
