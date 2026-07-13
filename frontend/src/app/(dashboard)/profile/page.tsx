"use client";

import React from "react";
import { useAuth } from "../../../context/AuthContext";
import { User as UserIcon, Mail, Shield, Building2, Clock } from "lucide-react";
import { motion } from "framer-motion";

export default function ProfilePage() {
  const { user, activeOrg } = useAuth();

  if (!user) return null;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div className="border-b border-neutral-900 pb-6">
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Operator Profile</h1>
        <p className="text-neutral-400 text-sm mt-1 leading-normal">
          Manage your enterprise credentials and security clearances.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Card */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="col-span-1 border border-neutral-900 bg-neutral-900/20 p-6 rounded-3xl backdrop-blur-md flex flex-col items-center text-center shadow-2xl relative overflow-hidden"
        >
          <div className="absolute top-0 w-full h-24 bg-gradient-to-b from-indigo-900/20 to-transparent" />
          
          <div className="w-24 h-24 rounded-2xl bg-neutral-950 border border-neutral-800 flex items-center justify-center text-indigo-400 text-4xl font-bold shadow-inner relative z-10 mb-4">
            {user.name.charAt(0).toUpperCase()}
          </div>
          
          <h2 className="text-xl font-bold text-white relative z-10">{user.name}</h2>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mt-2 relative z-10">
            Active Operator
          </span>
          
          <div className="w-full border-t border-neutral-900 mt-6 pt-4 space-y-3 text-left relative z-10">
            <div className="flex items-center gap-3 text-sm text-neutral-400">
              <Mail className="w-4 h-4 text-neutral-500" />
              <span className="truncate">{user.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-neutral-400">
              <Shield className="w-4 h-4 text-neutral-500" />
              <span>Standard Clearance</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-neutral-400">
              <Building2 className="w-4 h-4 text-neutral-500" />
              <span className="truncate">{activeOrg?.name || "No Organization"}</span>
            </div>
          </div>
        </motion.div>

        {/* Details & Security */}
        <div className="col-span-1 md:col-span-2 space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: 15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="border border-neutral-900 bg-neutral-900/10 p-6 rounded-2xl backdrop-blur-md"
          >
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <UserIcon className="w-4 h-4 text-indigo-400" />
              Personal Details
            </h3>
            
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-2">Full Name</label>
                  <input
                    type="text"
                    defaultValue={user.name}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-2.5 text-sm text-neutral-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-2">Email Address</label>
                  <input
                    type="email"
                    defaultValue={user.email}
                    disabled
                    className="w-full bg-neutral-950 border border-neutral-900 rounded-xl px-4 py-2.5 text-sm text-neutral-500 cursor-not-allowed"
                  />
                </div>
              </div>
              
              <div className="flex justify-end mt-4">
                <button
                  type="button"
                  className="px-4 py-2 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 rounded-xl text-xs font-semibold transition-all border border-indigo-600/30"
                >
                  Update Profile
                </button>
              </div>
            </form>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="border border-neutral-900 bg-neutral-900/10 p-6 rounded-2xl backdrop-blur-md"
          >
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Session Activity
            </h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <div>
                  <p className="text-xs font-semibold text-neutral-200">Windows • Chrome</p>
                  <p className="text-[10px] text-neutral-500">IP: 192.168.1.1 (Current Session)</p>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">Active</span>
              </div>
            </div>
            
            <div className="mt-5 border-t border-neutral-900 pt-5">
              <button className="text-xs font-semibold text-red-400 hover:text-red-300 transition-colors">
                Sign out of all other sessions
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
