"use client";

import Link from "next/link";
import { Brain, SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex h-screen w-screen bg-neutral-950 items-center justify-center text-neutral-100 p-6 overflow-hidden relative">
      {/* Decorative blurred backdrop */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-md w-full bg-neutral-900/60 border border-neutral-800 p-10 rounded-3xl shadow-2xl backdrop-blur-xl flex flex-col items-center text-center relative z-10 animate-in fade-in zoom-in-95 duration-500">
        <div className="w-16 h-16 bg-neutral-950 border border-neutral-800 rounded-2xl flex items-center justify-center text-indigo-400 mb-6 shadow-inner">
          <SearchX className="w-8 h-8" />
        </div>
        
        <h1 className="text-4xl font-extrabold text-white tracking-tight mb-2">404</h1>
        <h2 className="text-xl font-bold text-neutral-200 mb-4">Neural Pathway Not Found</h2>
        
        <p className="text-sm text-neutral-400 mb-8 leading-relaxed">
          The requested operational vector could not be located in the current workspace domain. Please verify your access or return to the central command dashboard.
        </p>
        
        <Link 
          href="/dashboard"
          className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)]"
        >
          <Brain className="w-4 h-4" />
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
