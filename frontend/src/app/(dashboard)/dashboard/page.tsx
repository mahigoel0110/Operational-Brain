"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { api } from "../../../lib/api";
import { Building2, FolderKanban, ArrowRight, ShieldAlert, Activity, FileText, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';

const maintenanceData = [
  { name: 'Jan', failures: 12, predicted: 14 },
  { name: 'Feb', failures: 19, predicted: 18 },
  { name: 'Mar', failures: 15, predicted: 16 },
  { name: 'Apr', failures: 10, predicted: 12 },
  { name: 'May', failures: 8, predicted: 10 },
  { name: 'Jun', failures: 14, predicted: 13 },
];

const assetDistribution = [
  { name: 'Mechanical', value: 400, color: '#4f46e5' },
  { name: 'Electrical', value: 300, color: '#06b6d4' },
  { name: 'Instrumentation', value: 300, color: '#8b5cf6' },
  { name: 'Process', value: 200, color: '#f59e0b' },
];

export default function DashboardPage() {
  const { workspaces, activeWorkspace, activeOrg } = useAuth();
  const [summary, setSummary] = useState<any>({
    document_count: 0,
    chunk_count: 0,
    knowledge_score: 0.0,
  });

  const [health, setHealth] = useState<any>({
    health_score: 0,
    readiness_indicator: "Loading",
  });

  useEffect(() => {
    if (activeWorkspace) {
      api.get(`/documents/workspace/${activeWorkspace.id}/knowledge-summary`)
        .then(res => setSummary(res.data))
        .catch(console.error);
        
      api.get(`/documents/workspace/${activeWorkspace.id}/knowledge-health`)
        .then(res => setHealth(res.data))
        .catch(console.error);
    }
  }, [activeWorkspace]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Documents</span>
            <FileText className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-3xl font-extrabold text-white">{summary.document_count || 128540}</h3>
            <p className="text-[11px] text-emerald-400 mt-1 font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> +12% this month
            </p>
          </div>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-[11px] font-bold uppercase tracking-wider">Assets Tracked</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-3xl font-extrabold text-white">6,215</h3>
            <p className="text-[11px] text-emerald-400 mt-1 font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> +8% this month
            </p>
          </div>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-[11px] font-bold uppercase tracking-wider">Work Orders</span>
            <FolderKanban className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 className="text-3xl font-extrabold text-white">1,243</h3>
            <p className="text-[11px] text-emerald-400 mt-1 font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> +18% this month
            </p>
          </div>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-[11px] font-bold uppercase tracking-wider">Compliance Score</span>
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-3xl font-extrabold text-white">
              {health.health_score > 0 ? health.health_score : 92}%
            </h3>
            <p className="text-[11px] text-emerald-400 mt-1 font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> +5% this month
            </p>
          </div>
        </div>
      </div>

      {/* 12 Column Grid for Complex Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Operational Health (Col Span 4) */}
        <div className="glass-card p-6 lg:col-span-4 flex flex-col">
          <h3 className="text-sm font-bold text-white mb-6">Operational Health</h3>
          <div className="flex-1 flex flex-col items-center justify-center relative">
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" className="stroke-slate-800" strokeWidth="8" fill="transparent" />
              <circle
                cx="50" cy="50" r="40"
                className="stroke-emerald-500" strokeWidth="8" fill="transparent"
                strokeDasharray="251.2"
                strokeDashoffset={251.2 - (251.2 * 0.78)}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-extrabold text-white">78</span>
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-1">Overall</span>
            </div>
          </div>
          <div className="mt-6 space-y-3">
            {[
              { label: 'Assets', val: 75, color: 'bg-indigo-500' },
              { label: 'Maintenance', val: 82, color: 'bg-cyan-500' },
              { label: 'Compliance', val: 92, color: 'bg-emerald-500' },
              { label: 'Quality', val: 71, color: 'bg-purple-500' },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-[11px] font-semibold text-slate-300 mb-1">
                  <span>{item.label}</span>
                  <span>{item.val}%</span>
                </div>
                <div className="w-full bg-slate-800/50 rounded-full h-1.5">
                  <div className={`${item.color} h-1.5 rounded-full`} style={{ width: `${item.val}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Maintenance Trend (Col Span 5) */}
        <div className="glass-card p-6 lg:col-span-5 flex flex-col">
          <h3 className="text-sm font-bold text-white mb-6">Maintenance Failure Trend</h3>
          <div className="flex-1 min-h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={maintenanceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }} />
                <Line type="monotone" dataKey="failures" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, fill: '#06b6d4', strokeWidth: 0 }} name="Actual Failures" />
                <Line type="monotone" dataKey="predicted" stroke="#6366f1" strokeWidth={2} strokeDasharray="5 5" dot={false} name="AI Predicted" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts Feed (Col Span 3) */}
        <div className="glass-card p-6 lg:col-span-3 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-white">Critical Alerts</h3>
            <Link href="#" className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold uppercase tracking-wider">View All</Link>
          </div>
          <div className="space-y-4 flex-1 overflow-y-auto pr-1 hide-scrollbar">
            {[
              { title: "High vibration detected in Pump P-101", time: "10 mins ago", level: "High", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
              { title: "Inspection overdue for Boiler B-202", time: "2 hours ago", level: "Medium", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
              { title: "SOP not followed in Work Order #8432", time: "3 hours ago", level: "High", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
              { title: "Oil analysis abnormal for Turbine T-305", time: "5 hours ago", level: "Medium", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
              { title: "Compliance document expired: PESO License", time: "6 hours ago", level: "High", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" }
            ].map((alert, i) => (
              <div key={i} className="flex gap-3 items-start pb-3 border-b border-slate-800/50 last:border-0">
                <AlertTriangle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${alert.color}`} />
                <div>
                  <p className="text-xs font-semibold text-slate-200 leading-snug">{alert.title}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[9px] text-slate-500">{alert.time}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${alert.bg} ${alert.color}`}>{alert.level}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Top Assets by Criticality */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-bold text-white mb-4">Top Assets by Criticality</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs">
                  <th className="pb-3 font-semibold">Asset Tag</th>
                  <th className="pb-3 font-semibold">Asset Name</th>
                  <th className="pb-3 font-semibold">Criticality</th>
                  <th className="pb-3 font-semibold">Health</th>
                  <th className="pb-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {[
                  { tag: "P-101", name: "Pump P-101", crit: "High", health: "72%", status: "Active", col: "text-red-400" },
                  { tag: "B-202", name: "Boiler B-202", crit: "High", health: "65%", status: "Active", col: "text-red-400" },
                  { tag: "T-305", name: "Turbine T-305", crit: "Very High", health: "45%", status: "At Risk", col: "text-rose-500" },
                  { tag: "C-401", name: "Compressor C-401", crit: "Medium", health: "88%", status: "Active", col: "text-amber-400" },
                ].map(row => (
                  <tr key={row.tag} className="text-slate-300 group hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 font-medium text-slate-200 group-hover:text-white">{row.tag}</td>
                    <td className="py-3 text-xs">{row.name}</td>
                    <td className={`py-3 text-xs font-semibold ${row.col}`}>{row.crit}</td>
                    <td className="py-3 text-xs font-semibold text-emerald-400">{row.health}</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-slate-300">
                        <span className={`w-1.5 h-1.5 rounded-full ${row.status === 'At Risk' ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`}></span>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Asset Distribution */}
        <div className="glass-card p-6 flex flex-col">
          <h3 className="text-sm font-bold text-white mb-4">Asset Distribution by Category</h3>
          <div className="flex-1 flex items-center justify-center">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={assetDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {assetDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Legend 
                  layout="vertical" 
                  verticalAlign="middle" 
                  align="right"
                  wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

