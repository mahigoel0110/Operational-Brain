import React from "react";
import { Search, Filter, Layout, Calendar, BarChart2, CheckSquare, Square, ChevronDown } from "lucide-react";

interface GraphControlsProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  searchSuggestions: any[];
  onSelectSuggestion: (id: string) => void;
  layoutName: string;
  setLayoutName: (name: string) => void;
  timeline: string;
  setTimeline: (t: string) => void;
  filters: Record<string, boolean>;
  toggleFilter: (type: string) => void;
  stats: any;
}

export default function GraphControls({
  searchQuery,
  setSearchQuery,
  searchSuggestions,
  onSelectSuggestion,
  layoutName,
  setLayoutName,
  timeline,
  setTimeline,
  filters,
  toggleFilter,
  stats
}: GraphControlsProps) {
  
  const layoutOptions = ["cose", "circle", "grid", "concentric", "breadthfirst"];
  const timelineOptions = ["Today", "Last Week", "Last Month", "All Time"];

  return (
    <div className="w-64 flex flex-col gap-4 overflow-y-auto custom-scrollbar shrink-0 h-full">
      {/* Search Autocomplete */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3 relative">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Search className="w-4 h-4 text-indigo-400" />
          Find Asset
        </h3>
        <div className="relative">
          <input
            type="text"
            placeholder="Type to search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg pl-3 pr-8 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
          {searchSuggestions.length > 0 && searchQuery && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden z-50 shadow-xl max-h-48 overflow-y-auto">
              {searchSuggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectSuggestion(s.id)}
                  className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors truncate"
                >
                  <span className="font-semibold text-indigo-300 mr-2">{s.type}</span>
                  {s.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Graph Layout Switcher */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Layout className="w-4 h-4 text-indigo-400" />
          Graph Layout
        </h3>
        <div className="relative">
          <select
            value={layoutName}
            onChange={(e) => setLayoutName(e.target.value)}
            className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg pl-3 pr-8 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 appearance-none capitalize"
          >
            {layoutOptions.map((opt) => (
              <option key={opt} value={opt} className="bg-slate-800">{opt === 'cose' ? 'Force Directed' : opt}</option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-2.5 pointer-events-none" />
        </div>
      </div>

      {/* Timeline Filter */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Calendar className="w-4 h-4 text-indigo-400" />
          Timeline
        </h3>
        <div className="flex flex-wrap gap-2">
          {timelineOptions.map((opt) => (
            <button
              key={opt}
              onClick={() => setTimeline(opt)}
              className={`text-[10px] font-bold px-3 py-1.5 rounded-lg border transition-colors ${
                timeline === opt
                  ? "bg-indigo-500/20 border-indigo-500 text-indigo-300"
                  : "bg-slate-900/50 border-slate-700 text-slate-400 hover:border-slate-600"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Toggles */}
      <div className="glass-card p-4 rounded-xl flex flex-col gap-3">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Filter className="w-4 h-4 text-indigo-400" />
          Filters
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
                <Square className="w-4 h-4 text-slate-500" />
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
          Live Statistics
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Equipment</span>
            <span className="font-bold text-white text-sm">{stats.equipment || 0}</span>
          </div>
          <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Documents</span>
            <span className="font-bold text-white text-sm">{stats.documents || 0}</span>
          </div>
          <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Relationships</span>
            <span className="font-bold text-white text-sm">{stats.edges || 0}</span>
          </div>
          <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
            <span className="block text-slate-500 mb-1">Density</span>
            <span className="font-bold text-white text-sm">{stats.density || '0.00'}</span>
          </div>
        </div>
      </div>

    </div>
  );
}
