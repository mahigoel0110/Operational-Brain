"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../../../context/AuthContext";
import { api, formatError } from "../../../../lib/api";
import {
  FileText, UploadCloud, Trash2, Download, AlertCircle, CheckCircle2,
  Loader2, FolderOpen, ArrowRight, TrendingUp, Brain, Gauge,
  Search, Database, Activity, FileQuestion, Network, RefreshCw, Info, Lock
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import CopilotTab from "./CopilotTab";
import KnowledgeGapTab from "./KnowledgeGapTab";
import InterviewTab from "./InterviewTab";
import GraphTab from "./GraphTab";
import MaintenanceTab from "./MaintenanceTab";

interface DocumentItem {
  id: string;
  name: string;
  workspace_id: string;
  uploaded_by: string;
  storage_path: string;
  file_size: number;
  status: string;
  version: string;
  mime_type: string | null;
  chunk_count: number;
  embedding_count: number;
  metadata: any;
  knowledge_score: number;
  processing_progress: number;
  current_step: string;
  error_message: string | null;
  department: string | null;
  created_at: string;
  updated_at: string;
}

// ─────────────────────────────────────────────────────────
// Placeholder Module Component
// ─────────────────────────────────────────────────────────
const PlaceholderModule = ({ title, description, icon: Icon }: { title: string; description: string; icon: any }) => (
  <div className="flex h-[60vh] items-center justify-center animate-in fade-in zoom-in-95 duration-300">
    <div className="glass-card p-12 text-center max-w-md w-full flex flex-col items-center">
      <div className="w-16 h-16 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
        <Icon className="w-8 h-8 text-indigo-400" />
      </div>
      <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
      <p className="text-sm text-slate-400 mb-8 leading-relaxed">
        {description}
      </p>
      <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-full border border-emerald-500/20">
        <Lock className="w-3.5 h-3.5" />
        Backend API Module Pending
      </div>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────
// Main Workspace Shell Page
// ─────────────────────────────────────────────────────────
export default function WorkspaceDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { workspaces, activeWorkspace, setActiveWorkspace } = useAuth();
  
  const workspaceId = params.id as string;
  const currentModule = searchParams.get("module") || "library";

  const [workspace, setWorkspace] = useState<any>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);
  const [loadingDocs, setLoadingDocs] = useState(true);

  // Upload states
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadStageIdx, setUploadStageIdx] = useState(-1);
  const [simulatedDocProps, setSimulatedDocProps] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Demo Mode
  const [demoMode, setDemoMode] = useState(true);
  const UPLOAD_STAGES = ["Uploaded", "Extracting Text", "OCR", "Metadata Extraction", "Chunking", "Embedding", "Vector Indexing", "READY"];

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchSummary, setSearchSummary] = useState<string | null>(null);

  // Selected document for metadata view
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);

  // Sync workspace metadata
  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoadingWorkspace(true);
        const res = await api.get(`/workspaces/${workspaceId}`);
        setWorkspace(res.data);
        const found = workspaces.find((w) => w.id === workspaceId);
        if (found) setActiveWorkspace(found);
      } catch (err) {
        console.error("Failed to fetch workspace:", err);
      } finally {
        setLoadingWorkspace(false);
      }
    };
    if (workspaceId) fetchWorkspace();
  }, [workspaceId, workspaces, setActiveWorkspace]);

  // Load documents
  const fetchDocuments = async () => {
    try {
      setLoadingDocs(true);
      const res = await api.get(`/documents/?workspace_id=${workspaceId}`);
      setDocuments(res.data);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (workspaceId) {
      fetchDocuments();
    }
  }, [workspaceId]);

  // Poll for document status
  useEffect(() => {
    const isProcessing = documents.some(
      (doc) => doc.status !== "READY" && doc.status !== "FAILED"
    );

    if (isProcessing) {
      const interval = setInterval(async () => {
        try {
          const res = await api.get(`/documents/?workspace_id=${workspaceId}`);
          setDocuments(res.data);
        } catch (err) {}
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [documents, workspaceId]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];

    if (file.size > 20 * 1024 * 1024) {
      setUploadError("File exceeds 20MB limit.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("workspace_id", workspaceId);

    try {
      if (demoMode) {
        // Start simulated demo pipeline
        setUploadStageIdx(0);
        let currentIdx = 0;
        const interval = setInterval(() => {
          currentIdx++;
          if (currentIdx < UPLOAD_STAGES.length) {
            setUploadStageIdx(currentIdx);
          } else {
            clearInterval(interval);
          }
        }, 800);
      }

      await api.post("/documents/", formData, {
        transformRequest: (data, headers) => {
          delete headers["Content-Type"];
          return data;
        }
      });
      
      if (!demoMode) {
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);
      } else {
        // Wait for animation to hit READY
        setTimeout(() => {
          setUploadStageIdx(UPLOAD_STAGES.length - 1);
          setSimulatedDocProps({
            chunks: Math.floor(Math.random() * 50) + 100,
            equipment: ["Pump P-451", "Valve V-21"],
            score: 96
          });
          setUploadSuccess(true);
          setTimeout(() => {
             setUploadSuccess(false);
             setUploadStageIdx(-1);
             setSimulatedDocProps(null);
          }, 6000); // stay visible longer in demo mode
        }, UPLOAD_STAGES.length * 800);
      }

      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchDocuments();
    } catch (err: any) {
      setUploadError(formatError(err, "Upload failed. Verify that file extension is supported."));
      setUploadStageIdx(-1);
    } finally {
      if (!demoMode) {
        setUploading(false);
      } else {
         setTimeout(() => setUploading(false), UPLOAD_STAGES.length * 800);
      }
    }
  };

  const handleViewDocument = async (doc: DocumentItem) => {
    try {
      const res = await api.get(`/documents/${doc.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: doc.mime_type || 'application/pdf' }));
      window.open(url, '_blank');
    } catch (err) {
      console.error("Failed to view document", err);
      alert("Failed to view document. It may still be processing.");
    }
  };

  const handleDeleteDocument = async (doc: DocumentItem) => {
    if (!confirm(`Are you sure you want to delete "${doc.name}"? This action cannot be undone.`)) return;
    try {
      await api.delete(`/documents/${doc.id}`);
      await fetchDocuments();
    } catch (err) {
      console.error("Failed to delete document", err);
      alert("Failed to delete document.");
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchSummary(null);
    try {
      const res = await api.post(`/documents/workspace/${workspaceId}/search`, { query: searchQuery, limit: 5 });
      setSearchResults(res.data.results);
      if (res.data.ai_summary) {
        setSearchSummary(res.data.ai_summary);
      }
    } catch (err: any) {} 
    finally { setSearching(false); }
  };

  const executeSearch = async (query: string) => {
    setSearchQuery(query);
    setSearching(true);
    setSearchSummary(null);
    setSelectedDoc(null);
    router.push(`?module=search`);
    try {
      const res = await api.post(`/documents/workspace/${workspaceId}/search`, { query, limit: 5 });
      setSearchResults(res.data.results);
      if (res.data.ai_summary) {
        setSearchSummary(res.data.ai_summary);
      }
    } catch (err: any) {} 
    finally { setSearching(false); }
  };

  if (loadingWorkspace) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-sm">Loading module context...</p>
        </div>
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    if (!+bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getStatusDetails = (status: string) => {
    switch (status?.toUpperCase()) {
      case "UPLOADED": return { text: "Uploaded", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" };
      case "EXTRACTING":
      case "OCR":
      case "METADATA":
      case "CHUNKING":
      case "EMBEDDING":
      case "INDEXING": return { text: status.charAt(0).toUpperCase() + status.slice(1).toLowerCase(), color: "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse" };
      case "READY": return { text: "Ready", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
      case "FAILED": return { text: "Failed", color: "bg-red-500/10 text-red-400 border-red-500/20" };
      default: return { text: "Unknown", color: "bg-slate-800 text-slate-400 border-slate-700" };
    }
  };

  // ─────────────────────────────────────────────────────────
  // Module Rendering Logic
  // ─────────────────────────────────────────────────────────
  
  if (currentModule === "expert") {
    return (
      <div className="animate-in fade-in duration-300">
        <CopilotTab workspaceId={workspaceId} documents={documents} />
      </div>
    );
  }

  if (currentModule === "coverage") {
    return (
      <div className="animate-in fade-in duration-300">
        <KnowledgeGapTab workspaceId={workspaceId} />
      </div>
    );
  }

  if (currentModule === "interview") {
    return (
      <div className="animate-in fade-in duration-300">
        <InterviewTab />
      </div>
    );
  }

  if (currentModule === "graph") {
    return (
      <div className="animate-in fade-in duration-300">
        <GraphTab workspaceId={workspaceId} />
      </div>
    );
  }

  if (currentModule === "maintenance") {
    return (
      <div className="animate-in fade-in duration-300 h-full">
        <MaintenanceTab workspaceId={workspaceId} />
      </div>
    );
  }

  if (["compliance", "lessons", "reports", "alerts", "settings"].includes(currentModule)) {
    return (
      <PlaceholderModule 
        title={`${currentModule.charAt(0).toUpperCase() + currentModule.slice(1)} Module`} 
        description="This enterprise module is currently being configured for Reliance Oil & Gas. Real-time integrations with SAP and Maximo are pending."
        icon={Network} 
      />
    );
  }

  if (currentModule === "search") {
    return (
      <div className="space-y-6 animate-in fade-in duration-300 max-w-4xl mx-auto pt-8">
        <div className="glass-card p-8 text-center space-y-6">
          <div className="w-16 h-16 bg-slate-900 border border-slate-800 rounded-full flex items-center justify-center mx-auto shadow-inner">
            <Search className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Industrial Semantic Search</h2>
            <p className="text-sm text-slate-400">Search through thousands of P&IDs, manuals, and procedures instantly.</p>
          </div>
          <form onSubmit={handleSearch} className="flex gap-3 max-w-2xl mx-auto relative">
            <input
              type="text"
              required
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. What is the emergency shutdown procedure for Boiler 3?"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-6 pr-4 py-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors shadow-inner"
            />
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="absolute right-2 top-2 bottom-2 px-6 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all disabled:opacity-50"
            >
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
            </button>
          </form>
        </div>

        <AnimatePresence mode="wait">
          {searchResults.length > 0 ? (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
              
              {searchSummary && (
                <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                  <div className="flex items-center gap-2 mb-4 text-emerald-400 font-bold uppercase tracking-widest text-xs">
                    <Brain className="w-4 h-4" />
                    Deterministic AI Summary
                  </div>
                  <div className="prose prose-invert prose-emerald max-w-none prose-sm font-sans leading-relaxed">
                    <ReactMarkdown>{searchSummary}</ReactMarkdown>
                  </div>
                </div>
              )}

              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wide px-1">Neural Search Results</h3>
              <div className="space-y-4">
                {searchResults.map((res, index) => (
                  <div key={res.id || index} className="glass-card p-6 relative overflow-hidden group border border-slate-800 hover:border-indigo-500/50 transition-colors">
                    <div className="absolute right-0 top-0 bottom-0 w-1 bg-indigo-600/30 group-hover:bg-indigo-500 transition-colors" />
                    
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className="w-4 h-4 text-indigo-400" />
                          <h4 className="text-sm font-bold text-slate-200">{res.title || "Unknown Document"}</h4>
                        </div>
                        <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                          <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800">Page {res.page_number || "N/A"}</span>
                          {res.department && <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800">{res.department}</span>}
                          {res.heading && <span className="bg-indigo-950/50 text-indigo-400 px-2 py-0.5 rounded border border-indigo-900/50 truncate max-w-[200px]">{res.heading}</span>}
                        </div>
                      </div>
                      
                      <div className="text-right flex flex-col items-end">
                        <span className="text-xl font-extrabold text-emerald-400">{Math.round((res.ranked_score || res.score) * 100)}%</span>
                        <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Similarity</span>
                      </div>
                    </div>
                    
                    <p className="text-slate-300 text-sm leading-relaxed font-mono bg-slate-900/50 p-4 rounded-xl border border-slate-800/80 mb-4 line-clamp-3">
                      "{res.text}"
                    </p>
                    
                    <div className="flex justify-end">
                      <button 
                        onClick={() => {
                          const doc = documents.find(d => d.id === (res.document_id || res.doc_id));
                          if (doc) setSelectedDoc(doc);
                        }}
                        className="flex items-center gap-2 text-xs font-bold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-4 py-2 rounded-lg border border-indigo-500/20 transition-colors"
                      >
                        <Info className="w-3.5 h-3.5" />
                        Open Document Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ) : (
            searchQuery && !searching && (
              <motion.div key="no-results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center p-12 text-slate-400 glass-card">
                <FileQuestion className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-slate-300 mb-2">No matching knowledge found.</h3>
                <p className="text-sm">Try using different keywords or broadening your search.</p>
              </motion.div>
            )
          )}
        </AnimatePresence>
      </div>
    );
  }

  // DEFAULT: Library
  return (
    <div className="animate-in fade-in duration-300 grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Document Library (Col 2) */}
      <div className="lg:col-span-2 space-y-6">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-lg font-bold text-white">Enterprise Knowledge Library</h2>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-bold uppercase">Demo Mode</span>
            <button 
              onClick={() => setDemoMode(!demoMode)}
              className={`w-10 h-5 rounded-full relative transition-colors ${demoMode ? 'bg-emerald-500' : 'bg-slate-700'}`}
            >
              <div className={`absolute top-1 w-3 h-3 rounded-full bg-white transition-all ${demoMode ? 'left-6' : 'left-1'}`} />
            </button>
          </div>
        </div>
        
        {loadingDocs ? (
          <div className="p-16 text-center text-slate-500 flex flex-col items-center glass-card">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
            <span className="text-sm font-semibold">Loading Enterprise Repository...</span>
          </div>
        ) : documents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => {
              const status = getStatusDetails(doc.status);
              const metadata = doc.metadata || {};
              const eqFound = metadata.equipment || [];
              
              return (
                <div key={doc.id} className="glass-card p-5 border border-slate-800 hover:border-indigo-500/30 transition-all flex flex-col relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-full h-1 bg-slate-800 group-hover:bg-indigo-500/50 transition-colors" />
                  
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-indigo-500/10 rounded-lg flex items-center justify-center border border-indigo-500/20">
                        <FileText className="w-5 h-5 text-indigo-400" />
                      </div>
                      <div>
                        <h3 
                          className="font-bold text-slate-200 text-sm truncate max-w-[160px] cursor-pointer hover:text-indigo-400"
                          onClick={() => setSelectedDoc(doc)}
                        >
                          {doc.name}
                        </h3>
                        <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mt-0.5">
                          {doc.department || "General"}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-[9px] font-black uppercase tracking-widest border ${status.color}`}>
                      {status.text}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-4 bg-slate-900/50 rounded-lg p-3 border border-slate-800/50">
                    <div className="text-center">
                      <span className="block text-lg font-black text-white">{doc.chunk_count}</span>
                      <span className="block text-[9px] text-slate-500 uppercase tracking-widest font-bold">Chunks</span>
                    </div>
                    <div className="text-center border-l border-slate-800/80">
                      <span className="block text-lg font-black text-indigo-400">{eqFound.length}</span>
                      <span className="block text-[9px] text-slate-500 uppercase tracking-widest font-bold">Assets</span>
                    </div>
                    <div className="text-center border-l border-slate-800/80">
                      <span className="block text-lg font-black text-emerald-400">{Math.round(doc.knowledge_score * 100)}%</span>
                      <span className="block text-[9px] text-slate-500 uppercase tracking-widest font-bold">Score</span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center mt-auto pt-2">
                    <span className="text-[10px] text-slate-600 font-mono">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                    <div className="flex items-center gap-1">
                       <button onClick={() => handleViewDocument(doc)} className="p-1.5 rounded bg-slate-900 text-slate-400 hover:text-white transition-colors">
                         <Download className="w-3.5 h-3.5" />
                       </button>
                       <button onClick={() => handleDeleteDocument(doc)} className="p-1.5 rounded bg-slate-900 text-slate-400 hover:text-red-400 transition-colors">
                         <Trash2 className="w-3.5 h-3.5" />
                       </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-16 text-center flex flex-col items-center justify-center glass-card">
            <FolderOpen className="w-12 h-12 text-slate-600 mb-4" />
            <h3 className="font-bold text-sm text-slate-300 mb-1">Repository Empty</h3>
            <p className="text-slate-500 text-xs max-w-sm">Upload standard operating procedures, manuals, or training materials to begin.</p>
          </div>
        )}
      </div>

      {/* Upload Pipeline (Col 1) */}
      <div className="space-y-6">
        <div className="glass-card p-8 flex flex-col items-center justify-center text-center relative overflow-hidden">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".pdf,.docx,.pptx,.xlsx,.txt,.png,.jpg,.jpeg"
            disabled={uploading}
          />
          
          {uploadStageIdx >= 0 && demoMode && !uploadSuccess ? (
            <div className="w-full flex flex-col items-center animate-in fade-in zoom-in-95 duration-300">
               <div className="w-16 h-16 rounded-full bg-indigo-500/20 flex items-center justify-center mb-6 border border-indigo-500/50">
                  <Activity className="w-8 h-8 text-indigo-400 animate-pulse" />
               </div>
               <h3 className="text-lg font-bold text-white mb-6">Processing Document</h3>
               <div className="w-full space-y-3">
                 {UPLOAD_STAGES.map((stage, idx) => {
                   const active = idx === uploadStageIdx;
                   const done = idx < uploadStageIdx;
                   return (
                     <div key={idx} className={`flex items-center gap-3 text-xs font-bold transition-all ${done ? 'text-emerald-400' : active ? 'text-indigo-400 scale-105' : 'text-slate-600 opacity-50'}`}>
                       {done ? <CheckCircle2 className="w-4 h-4" /> : active ? <Loader2 className="w-4 h-4 animate-spin" /> : <div className="w-4 h-4 rounded-full border-2 border-slate-700" />}
                       <span className="tracking-widest uppercase">{stage}</span>
                     </div>
                   );
                 })}
               </div>
            </div>
          ) : uploadSuccess && demoMode && simulatedDocProps ? (
            <div className="w-full flex flex-col items-center animate-in fade-in zoom-in-95 duration-300">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-4 border border-emerald-500/50">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
               </div>
               <h3 className="text-lg font-bold text-white mb-2">Successfully Indexed</h3>
               
               <div className="w-full bg-slate-900/50 rounded-xl border border-slate-800 p-4 space-y-4 text-left mt-4">
                 <div>
                   <span className="text-[10px] uppercase font-bold text-slate-500 block">Chunks Created</span>
                   <span className="text-2xl font-black text-indigo-400 flex items-center gap-2">
                     <BookOpen className="w-5 h-5" />
                     {simulatedDocProps.chunks}
                   </span>
                 </div>
                 
                 <div>
                   <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Equipment Detected</span>
                   <div className="flex flex-wrap gap-2">
                     {simulatedDocProps.equipment.map((eq: string, i: number) => (
                       <span key={i} className="px-2 py-1 bg-slate-800 rounded border border-slate-700 text-xs text-slate-300 font-bold">{eq}</span>
                     ))}
                   </div>
                 </div>
                 
                 <div>
                   <span className="text-[10px] uppercase font-bold text-slate-500 block">Knowledge Score</span>
                   <span className="text-lg font-black text-emerald-400">{simulatedDocProps.score}%</span>
                 </div>
               </div>
            </div>
          ) : (
            <>
              <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors ${uploading ? "bg-indigo-500/20 text-indigo-400 animate-pulse" : "bg-slate-900 text-slate-400 border border-slate-800"}`}>
                <UploadCloud className="w-10 h-10" />
              </div>

              <h3 className="font-bold text-base text-white mb-2">Ingestion Pipeline</h3>
              <p className="text-slate-400 text-xs mb-8">Upload documents to the secure enterprise vector store.</p>

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-bold transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] disabled:opacity-50 flex items-center justify-center gap-2 mb-4"
              >
                {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</> : "Select Document"}
              </button>
              
              <AnimatePresence>
                {uploadError && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="w-full p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex flex-col items-center justify-center gap-2 text-red-400 text-xs">
                    <AlertCircle className="w-4 h-4" />
                    <span>{uploadError}</span>
                  </motion.div>
                )}
                {uploadSuccess && !demoMode && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="w-full p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center gap-2 text-emerald-400 text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Document uploaded successfully!</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      </div>
      
      {/* Metadata Drawer */}
      <AnimatePresence>
        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-end">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedDoc(null)} />
            <motion.div
              initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ type: "tween", duration: 0.2 }}
              className="w-full max-w-md bg-slate-950 border-l border-slate-800 h-full relative z-50 flex flex-col p-8 overflow-y-auto"
            >
              <div className="flex justify-between items-center border-b border-slate-800/60 pb-6 mb-8">
                <h3 className="text-xl font-bold text-white">
                  {selectedDoc.metadata?.is_engineering_drawing ? "Engineering Drawing Intelligence" : "Document Metadata"}
                </h3>
                <button onClick={() => setSelectedDoc(null)} className="p-2 bg-slate-900 rounded-lg text-slate-400 hover:text-white transition-colors">Close</button>
              </div>
              <div className="space-y-6 pb-12">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Original File</span>
                  <p className="text-sm font-semibold text-white bg-slate-900 p-4 rounded-xl border border-slate-800">{selectedDoc.name}</p>
                </div>

                {selectedDoc.metadata?.is_engineering_drawing ? (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Drawing Type</span>
                        <span className="px-3 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg text-xs font-bold uppercase">{selectedDoc.metadata.drawing_type}</span>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Revision</span>
                        <span className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg text-xs font-bold uppercase">{selectedDoc.metadata.revision}</span>
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Confidence Score</span>
                      <p className="text-2xl font-extrabold text-emerald-400">{Math.round(selectedDoc.knowledge_score * 100)}%</p>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block flex justify-between items-center mb-2">
                        <span>Equipment Assets</span>
                        <span className="text-[9px] bg-slate-800 px-2 py-0.5 rounded text-slate-400 border border-slate-700 normal-case">Click to view related documents</span>
                      </span>
                      <div className="grid grid-cols-2 gap-2">
                        {selectedDoc.metadata?.equipment?.map((eq: any, i: number) => (
                          <button key={i} onClick={() => executeSearch(`${eq.type} ${eq.tag}`)} className="flex items-center gap-2 p-2 bg-slate-900/50 hover:bg-indigo-500/10 border border-slate-800 hover:border-indigo-500/50 rounded-lg text-left transition-colors group">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                            <div className="truncate">
                              <span className="block text-xs font-bold text-slate-200 group-hover:text-indigo-400 truncate">{eq.type} {eq.tag}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Instrumentation</span>
                      <div className="flex flex-wrap gap-2">
                        {selectedDoc.metadata?.instrumentation?.map((inst: any, i: number) => (
                          <span key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">
                            <Activity className="w-3 h-3 text-indigo-400 shrink-0" />
                            {inst.type} {inst.tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Knowledge Graph Connections</span>
                      <div className="space-y-2 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                        {selectedDoc.metadata?.relationships?.map((rel: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-slate-300 truncate max-w-[100px]">{rel.from}</span>
                            <span className="text-[9px] font-bold text-indigo-400 uppercase bg-indigo-500/10 px-2 py-0.5 rounded-full whitespace-nowrap mx-1 border border-indigo-500/20">
                              <ArrowRight className="w-3 h-3 inline mr-1"/>
                              {rel.relation}
                            </span>
                            <span className="font-semibold text-slate-300 truncate max-w-[100px]">{rel.to}</span>
                          </div>
                        ))}
                        {(!selectedDoc.metadata?.relationships || selectedDoc.metadata.relationships.length === 0) && (
                          <span className="text-xs text-slate-500 italic">No relationships detected.</span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Standards</span>
                        <div className="flex flex-wrap gap-2">
                          {selectedDoc.metadata?.standards?.map((s: string, i: number) => (
                            <span key={i} className="text-xs font-bold text-slate-400 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800">{s}</span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Line Numbers</span>
                        <div className="flex flex-wrap gap-2">
                          {selectedDoc.metadata?.line_numbers?.map((l: string, i: number) => (
                            <span key={i} className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-1 rounded border border-slate-800">{l}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Confidence Score</span>
                        <p className="text-2xl font-extrabold text-indigo-400">{Math.round(selectedDoc.knowledge_score * 100)}%</p>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Total Chunks</span>
                        <p className="text-2xl font-extrabold text-white">{selectedDoc.chunk_count}</p>
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Detected Department</span>
                      <p className="text-sm text-slate-300 font-semibold">{selectedDoc.metadata?.department || "Unassigned"}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Extracted Entities</span>
                      <div className="flex flex-wrap gap-2">
                        {selectedDoc.metadata?.machines?.map((m:string, i:number) => (
                          <span key={i} className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-bold">{m}</span>
                        ))}
                        {!selectedDoc.metadata?.machines?.length && <span className="text-xs text-slate-600 italic">No equipment tagged</span>}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
