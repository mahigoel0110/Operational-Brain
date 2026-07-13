"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useParams, usePathname, useSearchParams } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import {
  Brain,
  Search,
  LayoutDashboard,
  Bot,
  Database,
  ShieldCheck,
  TrendingUp,
  FileText,
  AlertTriangle,
  Settings,
  Menu,
  X,
  Upload,
  BarChart3,
  Network,
  Wrench,
  BookOpen,
  ChevronDown,
  Building2,
  LogOut,
  ClipboardList
} from "lucide-react";
import Link from "next/link";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const {
    user,
    token,
    loading,
    organizations,
    workspaces,
    activeOrg,
    activeWorkspace,
    setActiveOrg,
    setActiveWorkspace,
    createOrganization,
    createWorkspace,
    logout
  } = useAuth();

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const params = useParams();

  const currentModule = searchParams.get("module") || (pathname === "/dashboard" ? "dashboard" : "unknown");

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [deptMenuOpen, setDeptMenuOpen] = useState(false);
  
  const [globalSearch, setGlobalSearch] = useState("");

  const departments = [
    "Engineering", "Operations", "Maintenance", "Inspection", 
    "HSE", "Quality", "Projects", "Procurement", "Finance", "Human Resources"
  ];

  const [activeDept, setActiveDept] = useState("Operations");

  // Auth guard
  useEffect(() => {
    if (!loading && (!token || !user)) {
      router.push("/login");
    }
  }, [loading, token, user, router]);

  // Auto-setup organization if none exists
  useEffect(() => {
    if (!loading && organizations.length > 0 && !activeOrg) {
      // Find "Reliance Oil & Gas" or default to first
      const reliance = organizations.find((o: any) => o.name.includes("Reliance")) || organizations[0];
      setActiveOrg(reliance);
    }
  }, [loading, organizations, activeOrg, setActiveOrg]);

  // Auto-setup workspace if none exists
  useEffect(() => {
    if (!loading && workspaces.length > 0 && !activeWorkspace) {
      setActiveWorkspace(workspaces[0]);
    }
  }, [loading, workspaces, activeWorkspace, setActiveWorkspace]);

  if (loading || !user) {
    return (
      <div className="flex h-screen w-screen bg-slate-950 items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <Brain className="w-8 h-8 animate-pulse text-indigo-500" />
          <p className="text-sm font-medium tracking-wide">Initializing CEREBRO Enterprise...</p>
        </div>
      </div>
    );
  }

  const getWorkspaceHref = (mod: string) => {
    if (mod === "dashboard") return "/dashboard";
    if (mod === "settings") return "/settings";
    if (activeWorkspace) {
      return `/workspaces/${activeWorkspace.id}?module=${mod}`;
    }
    return `/dashboard?module=${mod}`;
  };

  const navItems = [
    { name: "Dashboard", icon: LayoutDashboard, module: "dashboard" },
    { name: "Industrial Expert", icon: Bot, module: "expert" },
    { name: "Knowledge Library", icon: Database, module: "library" },
    { name: "Industrial Search", icon: Search, module: "search" },
    { name: "Knowledge Coverage", icon: ShieldCheck, module: "coverage" },
    { name: "Interview", icon: ClipboardList, module: "interview" },
    { name: "Knowledge Graph", icon: Network, module: "graph" },
    { name: "Maintenance Intelligence", icon: Wrench, module: "maintenance" },
    { name: "Compliance Intelligence", icon: TrendingUp, module: "compliance" },
    { name: "Lessons Learned", icon: BookOpen, module: "lessons" },
    { name: "Reports", icon: FileText, module: "reports" },
    { name: "Alerts", icon: AlertTriangle, module: "alerts" },
    { name: "Settings", icon: Settings, module: "settings" },
  ];

  const currentNav = navItems.find((n) => n.module === currentModule) || navItems[0];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="md:hidden absolute inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Enterprise Left Sidebar */}
      <aside
        className={`fixed md:relative top-0 bottom-0 left-0 z-40 w-64 border-r border-slate-800/60 bg-slate-950/80 backdrop-blur-xl flex flex-col transition-transform duration-300 md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="h-16 border-b border-slate-800/60 px-6 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.4)]">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-lg tracking-tight text-white">
              CEREBRO
            </span>
          </Link>
          <button className="md:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation List */}
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-1 hide-scrollbar">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-4 px-2">
            Platform Modules
          </span>
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={getWorkspaceHref(item.module)}
              onClick={() => setSidebarOpen(false)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all group ${
                currentModule === item.module || (currentModule === "unknown" && pathname === item.module)
                  ? "bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-semibold shadow-inner"
                  : "border border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
              }`}
            >
              <item.icon className={`w-4 h-4 flex-shrink-0 ${currentModule === item.module ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"}`} />
              <span className="truncate">{item.name}</span>
            </Link>
          ))}
        </div>

        {/* Sidebar Footer User Profile */}
        <div className="p-4 border-t border-slate-800/60">
          <button
            onClick={logout}
            className="w-full flex items-center justify-between p-2 hover:bg-slate-900/60 rounded-xl transition-all group text-left"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400 font-bold shadow-inner flex-shrink-0">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-200 truncate">{user.name}</p>
                <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
              </div>
            </div>
            <LogOut className="w-4 h-4 text-slate-500 hover:text-red-400 transition-colors flex-shrink-0" />
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-800/60 flex items-center justify-between px-6 bg-slate-950/40 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center flex-1 gap-4">
            <button className="md:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            
            {/* Global Industrial Search */}
            <div className="max-w-xl w-full hidden md:flex items-center relative group">
              <Search className="w-4 h-4 text-slate-500 absolute left-4 group-focus-within:text-indigo-400 transition-colors" />
              <input
                type="text"
                value={globalSearch}
                onChange={(e) => setGlobalSearch(e.target.value)}
                placeholder="Global Industrial Search (Documents, Equipment, Assets...)"
                className="w-full bg-slate-900/50 border border-slate-800/80 rounded-full pl-11 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 focus:bg-slate-900 transition-all shadow-inner"
              />
              <div className="absolute right-3 flex items-center gap-1">
                <kbd className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-semibold text-slate-400 border border-slate-700">Ctrl</kbd>
                <kbd className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-semibold text-slate-400 border border-slate-700">K</kbd>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4 flex-shrink-0">
            {/* Auth Info / Notifications could go here */}
            <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center cursor-pointer hover:border-slate-600 transition-colors relative">
              <AlertTriangle className="w-4 h-4 text-slate-400" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-slate-950"></span>
            </div>
          </div>
        </header>

        {/* Workspace Header Context */}
        <div className="bg-slate-900/20 border-b border-slate-800/60 px-8 py-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            
            {/* Breadcrumb & Title */}
            <div>
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-500 mb-2">
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <Building2 className="w-3.5 h-3.5" />
                  Reliance Oil & Gas
                </span>
                <span className="text-slate-700">/</span>
                
                {/* Department Switcher */}
                <div className="relative">
                  <button 
                    onClick={() => setDeptMenuOpen(!deptMenuOpen)}
                    className="flex items-center gap-1 hover:text-slate-300 transition-colors"
                  >
                    {activeDept} <ChevronDown className="w-3 h-3" />
                  </button>
                  {deptMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setDeptMenuOpen(false)}></div>
                      <div className="absolute top-full left-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-1 z-50">
                        {departments.map((dept) => (
                          <button
                            key={dept}
                            onClick={() => { setActiveDept(dept); setDeptMenuOpen(false); }}
                            className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                              activeDept === dept ? "bg-indigo-600 text-white font-bold" : "text-slate-400 hover:bg-slate-800"
                            }`}
                          >
                            {dept}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>

                <span className="text-slate-700">/</span>
                <span className="text-slate-300">{currentNav.name}</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
                {currentNav.name}
              </h1>
              <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
                {currentNav.name === "Industrial Expert" && "Ask AI anything about your operational guidelines, manuals, and data."}
                {currentNav.name === "Knowledge Library" && "Centralized repository for all ingested operational manuals, P&IDs, and spreadsheets."}
                {currentNav.name === "Dashboard" && "Unified view of your active workspaces and operational health metrics."}
                {!["Industrial Expert", "Knowledge Library", "Dashboard"].includes(currentNav.name) && `Manage and analyze your ${currentNav.name.toLowerCase()} workflows.`}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href={getWorkspaceHref("library")}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 transition-all shadow-sm"
              >
                <Upload className="w-4 h-4" /> Upload
              </Link>
              <Link
                href={getWorkspaceHref("expert")}
                className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold text-white transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)]"
              >
                <Bot className="w-4 h-4" /> AI Copilot
              </Link>
              <Link
                href={getWorkspaceHref("graph")}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 transition-all shadow-sm"
              >
                <Network className="w-4 h-4" /> Graph
              </Link>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto bg-slate-950 p-6 md:p-8">
          <div className="max-w-[1600px] mx-auto w-full h-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
