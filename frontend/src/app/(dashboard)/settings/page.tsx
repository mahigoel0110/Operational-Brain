"use client";

import React, { useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Settings2, Bell, Shield, Database, Webhook, MonitorSmartphone, Palette } from "lucide-react";
import { motion } from "framer-motion";

export default function SettingsPage() {
  const { activeOrg } = useAuth();
  const [activeTab, setActiveTab] = useState("general");

  const tabs = [
    { id: "general", label: "General", icon: Settings2 },
    { id: "security", label: "Security & Auth", icon: Shield },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "api", label: "API & Webhooks", icon: Webhook },
    { id: "data", label: "Data Retention", icon: Database },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div className="border-b border-neutral-900 pb-6">
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">System Settings</h1>
        <p className="text-neutral-400 text-sm mt-1 leading-normal">
          Configure application preferences for {activeOrg?.name || "your organization"}.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar Nav */}
        <div className="w-full md:w-64 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 shadow-inner"
                      : "text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200 border border-transparent"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${activeTab === tab.id ? "text-indigo-400" : "text-neutral-500"}`} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1">
          {activeTab === "general" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="border border-neutral-900 bg-neutral-900/10 p-6 rounded-2xl backdrop-blur-md">
                <h3 className="text-sm font-bold text-white mb-4">Workspace Defaults</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-2">Default Department</label>
                    <select className="w-full max-w-sm bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-2.5 text-sm text-neutral-100 focus:outline-none focus:border-indigo-500">
                      <option>General Operations</option>
                      <option>Maintenance</option>
                      <option>Safety & Compliance</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-2">Timezone</label>
                    <select className="w-full max-w-sm bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-2.5 text-sm text-neutral-100 focus:outline-none focus:border-indigo-500">
                      <option>UTC (Coordinated Universal Time)</option>
                      <option>EST (Eastern Standard Time)</option>
                      <option>PST (Pacific Standard Time)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="border border-red-500/20 bg-red-500/5 p-6 rounded-2xl backdrop-blur-md">
                <h3 className="text-sm font-bold text-red-400 mb-2">Danger Zone</h3>
                <p className="text-xs text-neutral-400 mb-4">Permanent destructive actions regarding your organization.</p>
                <button className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-xs font-bold transition-colors border border-red-500/20">
                  Delete Organization
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === "appearance" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="border border-neutral-900 bg-neutral-900/10 p-6 rounded-2xl backdrop-blur-md">
                <h3 className="text-sm font-bold text-white mb-4">Theme Preferences</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="border-2 border-indigo-500 bg-neutral-950 p-4 rounded-xl cursor-pointer relative overflow-hidden">
                    <div className="absolute top-2 right-2 w-3 h-3 bg-indigo-500 rounded-full" />
                    <MonitorSmartphone className="w-6 h-6 text-indigo-400 mb-2" />
                    <span className="text-xs font-bold text-white">System Dark</span>
                    <p className="text-[10px] text-neutral-500 mt-1">Default glassmorphic UI</p>
                  </div>
                  <div className="border-2 border-transparent hover:border-neutral-700 bg-neutral-950 p-4 rounded-xl cursor-pointer opacity-50 transition-colors">
                    <MonitorSmartphone className="w-6 h-6 text-neutral-500 mb-2" />
                    <span className="text-xs font-bold text-white">Light Mode</span>
                    <p className="text-[10px] text-neutral-500 mt-1">Coming Soon</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab !== "general" && activeTab !== "appearance" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="border border-neutral-900 bg-neutral-900/10 p-12 rounded-2xl backdrop-blur-md text-center">
              <Settings2 className="w-12 h-12 text-neutral-700 mx-auto mb-4" />
              <h3 className="text-base font-bold text-white mb-1">Configuration Unavailable</h3>
              <p className="text-xs text-neutral-500">This settings module is locked in the current Phase 2 build.</p>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
