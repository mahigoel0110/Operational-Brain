import React, { useEffect, useRef } from "react";
import { ExternalLink, FileText, Wrench, Focus, Network, X } from "lucide-react";
import { motion } from "framer-motion";

interface ContextMenuProps {
  x: number;
  y: number;
  node: any;
  onClose: () => void;
  onExpand: (id: string) => void;
  onFocus: (id: string) => void;
}

export default function ContextMenu({ x, y, node, onClose, onExpand, onFocus }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  if (!node) return null;

  const isDocument = node.type === 'Document' || node.type === 'SOP' || node.type === 'P&ID' || node.type === 'Inspection';

  return (
    <motion.div
      ref={menuRef}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      style={{ top: y, left: x }}
      className="absolute z-50 w-56 bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-2xl overflow-hidden"
    >
      <div className="px-4 py-3 border-b border-slate-800/50 flex items-center justify-between">
        <span className="text-xs font-bold text-white truncate max-w-[140px]" title={node.label}>
          {node.label}
        </span>
        <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="py-1">
        {isDocument ? (
          <button
            onClick={() => {
              // Mock action
              console.log("Opening document:", node.id);
              onClose();
            }}
            className="w-full px-4 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-blue-400" />
            Open {node.type}
          </button>
        ) : (
          <button
            onClick={() => {
              // Mock action
              console.log("Viewing maintenance:", node.id);
              onClose();
            }}
            className="w-full px-4 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2 transition-colors"
          >
            <Wrench className="w-3.5 h-3.5 text-purple-400" />
            View Maintenance History
          </button>
        )}

        <button
          onClick={() => {
            onFocus(node.id);
            onClose();
          }}
          className="w-full px-4 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2 transition-colors"
        >
          <Focus className="w-3.5 h-3.5 text-teal-400" />
          Focus Node
        </button>

        <button
          onClick={() => {
            onExpand(node.id);
            onClose();
          }}
          className="w-full px-4 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2 transition-colors"
        >
          <Network className="w-3.5 h-3.5 text-indigo-400" />
          Expand Neighbors
        </button>
        
        <div className="h-px bg-slate-800/50 my-1"></div>
        
        <button
          onClick={() => {
            console.log("Opening external system for", node.id);
            onClose();
          }}
          className="w-full px-4 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2 transition-colors"
        >
          <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          View in External System
        </button>
      </div>
    </motion.div>
  );
}
