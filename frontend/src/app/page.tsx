"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Database, ShieldAlert, Cpu, Network, FileText } from "lucide-react";

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.5, ease: "easeOut" as const } }
  };

  return (
    <div className="flex flex-col min-h-screen bg-neutral-950 text-neutral-100 overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      {/* Decorative background grid and gradients */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      <div className="absolute top-0 right-0 -mt-24 -mr-24 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-0 -ml-24 w-96 h-96 rounded-full bg-emerald-500/5 blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="border-b border-neutral-800 bg-neutral-950/70 backdrop-blur-md sticky top-0 z-50 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="bg-indigo-600 p-2 rounded-lg group-hover:bg-indigo-500 transition-colors shadow-[0_0_15px_rgba(79,70,229,0.3)]">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-indigo-200 via-neutral-100 to-indigo-200 bg-clip-text text-transparent">
              CEREBRO
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-neutral-400 hover:text-neutral-100 transition-colors px-3.5 py-2 rounded-md hover:bg-neutral-900"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-all shadow-[0_0_20px_rgba(79,70,229,0.35)] hover:shadow-[0_0_25px_rgba(79,70,229,0.5)] flex items-center gap-1.5 hover:scale-[1.02]"
            >
              Get Started <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 md:py-24 flex flex-col justify-center relative z-10">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center max-w-4xl mx-auto flex flex-col items-center"
        >
          <motion.div
            variants={itemVariants}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/5 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-8"
          >
            <Cpu className="w-3.5 h-3.5 animate-pulse text-indigo-400" />
            Phase 1 Release - Foundations & Ingestion
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1] text-white"
          >
            Unified Industrial <br />
            <span className="bg-gradient-to-r from-indigo-400 via-indigo-200 to-emerald-400 bg-clip-text text-transparent">
              Operations Brain
            </span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="text-neutral-400 text-lg sm:text-xl max-w-2xl mb-12 leading-relaxed"
          >
            Organize departments, coordinate teams, and manage industrial assets. Secure, localized documentation repository built for operational intelligence.
          </motion.p>

          <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 mb-16 justify-center w-full sm:w-auto">
            <Link
              href="/signup"
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-8 py-4 rounded-xl transition-all shadow-[0_0_30px_rgba(79,70,229,0.4)] hover:shadow-[0_0_35px_rgba(79,70,229,0.6)] flex items-center justify-center gap-2 group hover:scale-[1.03] text-base"
            >
              Start Free Trial{" "}
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="border border-neutral-800 hover:border-neutral-700 bg-neutral-900/40 hover:bg-neutral-900/70 text-neutral-300 hover:text-white font-medium px-8 py-4 rounded-xl transition-all flex items-center justify-center gap-2 hover:scale-[1.03] text-base"
            >
              Sign In to Account
            </Link>
          </motion.div>

          {/* Feature Grid */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left mt-8"
          >
            {/* Feature 1 */}
            <div className="border border-neutral-800 bg-neutral-900/30 hover:bg-neutral-900/50 backdrop-blur-sm p-6 rounded-2xl transition-all duration-300 hover:border-neutral-700 hover:translate-y-[-4px] shadow-[0_4px_30px_rgba(0,0,0,0.1)] group">
              <div className="bg-indigo-500/10 text-indigo-400 p-3.5 rounded-xl w-fit mb-5 border border-indigo-500/20 group-hover:bg-indigo-500/20 transition-all shadow-[0_0_15px_rgba(99,102,241,0.1)]">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-white mb-2.5">Unified Workspaces</h3>
              <p className="text-neutral-400 text-sm leading-relaxed">
                Create structured organization units mapped to specific plants, departments, or maintenance squads.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="border border-neutral-800 bg-neutral-900/30 hover:bg-neutral-900/50 backdrop-blur-sm p-6 rounded-2xl transition-all duration-300 hover:border-neutral-700 hover:translate-y-[-4px] shadow-[0_4px_30px_rgba(0,0,0,0.1)] group">
              <div className="bg-emerald-500/10 text-emerald-400 p-3.5 rounded-xl w-fit mb-5 border border-emerald-500/20 group-hover:bg-emerald-500/20 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-white mb-2.5">Secure Document Library</h3>
              <p className="text-neutral-400 text-sm leading-relaxed">
                Secure local file hosting supporting PDFs, DOCX, PPTX, XLSX, and TXT files with auto-versioning and tags.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="border border-neutral-800 bg-neutral-900/30 hover:bg-neutral-900/50 backdrop-blur-sm p-6 rounded-2xl transition-all duration-300 hover:border-neutral-700 hover:translate-y-[-4px] shadow-[0_4px_30px_rgba(0,0,0,0.1)] group">
              <div className="bg-amber-500/10 text-amber-400 p-3.5 rounded-xl w-fit mb-5 border border-amber-500/20 group-hover:bg-amber-500/20 transition-all shadow-[0_0_15px_rgba(245,158,11,0.1)]">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-white mb-2.5">Enterprise RBAC</h3>
              <p className="text-neutral-400 text-sm leading-relaxed">
                Manage roles and keep sensitive operational documents completely isolated with owner validation checks.
              </p>
            </div>
          </motion.div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-900 py-8 bg-neutral-950/80 z-10 relative">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-neutral-500 text-xs">
          <span>&copy; {new Date().getFullYear()} CEREBRO. All rights reserved. Industrial Knowledge Intelligence.</span>
          <div className="flex gap-6 mt-4 md:mt-0">
            <span className="hover:text-neutral-300 cursor-pointer">Security Protocol</span>
            <span className="hover:text-neutral-300 cursor-pointer">Data Protection</span>
            <span className="hover:text-neutral-300 cursor-pointer">Local Sandbox</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
