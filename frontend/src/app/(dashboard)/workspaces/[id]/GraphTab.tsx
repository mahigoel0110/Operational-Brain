"use client";

import React, { useState, useEffect, useRef } from "react";
import { api } from "../../../../lib/api";
import { AnimatePresence } from "framer-motion";

// Graph Modular Components
import GraphCanvas from "./graph/GraphCanvas";
import GraphSidebar from "./graph/GraphSidebar";
import GraphRightPanel from "./graph/GraphRightPanel";
import ContextMenu from "./graph/ContextMenu";
import { GraphData, NodeDetails } from "./graph/types";

interface GraphTabProps {
  workspaceId: string;
}

export default function GraphTab({ workspaceId }: GraphTabProps) {
  const [data, setData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  
  // Graph Controls State
  const [searchQuery, setSearchQuery] = useState("");
  const [layoutName, setLayoutName] = useState("cose");
  const [timeline, setTimeline] = useState("All Time");
  const [filters, setFilters] = useState<Record<string, boolean>>({
    Equipment: true,
    Pump: true,
    Valve: true,
    Tank: true,
    Document: true,
    SOP: true,
    Maintenance: true,
    Inspection: true,
    "P&ID": true,
    People: true,
    Area: true,
  });
  
  // Interaction States
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [entityDetails, setEntityDetails] = useState<NodeDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, node: any } | null>(null);
  
  const cyRef = useRef<any>(null);

  useEffect(() => {
    fetchGraph();
  }, [workspaceId]);

  const fetchGraph = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/graph?workspace_id=${workspaceId}`);
      if (res.data && res.data.nodes && res.data.nodes.length > 0) {
        setData(res.data);
      } else {
        setData({ nodes: [], edges: [] });
      }
    } catch (err) {
      console.error("Error fetching graph:", err);
      setData({ nodes: [], edges: [] });
    } finally {
      setLoading(false);
    }
  };

  const toggleFilter = (type: string) => {
    setFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const handleNodeSelect = async (nodeData: any) => {
    setSelectedNode(nodeData);
    setEntityDetails(null);
    setContextMenu(null);
    
    // Highlight neighborhood visually in cytoscape
    if (cyRef.current) {
      const cy = cyRef.current;
      const node = cy.getElementById(nodeData.id);
      if (node) {
        cy.elements().removeClass('highlighted dimmed');
        cy.elements().addClass('dimmed');
        node.removeClass('dimmed').addClass('highlighted');
        node.neighborhood().removeClass('dimmed').addClass('highlighted');
      }
    }
    
    try {
      setLoadingDetails(true);
      const res = await api.get(`/api/graph/entity/${encodeURIComponent(nodeData.id)}`);
      if (res.data && Object.keys(res.data).length > 0) {
        setEntityDetails(res.data);
      } else {
        setEntityDetails(mockEntityDetails(nodeData));
      }
    } catch (err) {
      setEntityDetails(mockEntityDetails(nodeData));
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleNodeDoubleClick = async (nodeData: any) => {
    try {
      // Mock expansion: simply center and animate
      const cy = cyRef.current;
      if (cy) {
        const node = cy.getElementById(nodeData.id);
        cy.animate({
          center: { eles: node },
          zoom: 1.5,
          duration: 500
        });
      }
      // Wait for backend to support actual incremental expansion
      console.log(`Expanding ${nodeData.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchSelect = (id: string) => {
    if (!cyRef.current) return;
    const node = cyRef.current.getElementById(id);
    if (node) {
      cyRef.current.center(node);
      cyRef.current.zoom({ level: 1.5, position: node.position() });
      node.trigger('tap'); // Trigger select
    }
  };

  const handleBackgroundClick = () => {
    setSelectedNode(null);
    setEntityDetails(null);
    setContextMenu(null);
    if (cyRef.current) {
      cyRef.current.elements().removeClass('highlighted dimmed');
    }
  };

  return (
    <div className="flex h-[calc(100vh-140px)] gap-4 animate-in fade-in duration-300 relative">
      
      {/* 1. Left Panel (25%) */}
      <GraphSidebar 
        selectedNode={selectedNode}
        entityDetails={entityDetails}
        loadingDetails={loadingDetails}
      />

      {/* 2. Center Graph (50%) */}
      <div className="w-[50%] flex-1 relative min-h-0 z-10 shadow-2xl glass-card overflow-hidden">
        {data.nodes.length === 0 && !loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center bg-slate-900/50">
             <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4 border border-slate-700">
               <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500"><path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22v-8"/><path d="m3 21 8-8"/><path d="m21 21-8-8"/></svg>
             </div>
             <h3 className="text-lg font-bold text-slate-300 mb-2">No Entity Relationships Found</h3>
             <p className="text-sm text-slate-500 max-w-sm">No graph has been generated for the selected documents. Continue uploading documents to build the knowledge graph.</p>
          </div>
        ) : (
          <GraphCanvas 
            data={data}
            filters={filters}
            layoutName={layoutName}
            loading={loading}
            onNodeSelect={handleNodeSelect}
            onNodeDoubleClick={handleNodeDoubleClick}
            onBackgroundClick={handleBackgroundClick}
            onContextMenu={(x, y, node) => setContextMenu({ x, y, node })}
            cyRefHook={(cy) => (cyRef.current = cy)}
          />
        )}
      </div>

      {/* 3. Right Panel (25%) */}
      <GraphRightPanel
        data={data}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearchSelect={handleSearchSelect}
        layoutName={layoutName}
        setLayoutName={setLayoutName}
        timeline={timeline}
        setTimeline={setTimeline}
        filters={filters}
        toggleFilter={toggleFilter}
      />

      {/* 4. Context Menu */}
      <AnimatePresence>
        {contextMenu && (
          <ContextMenu 
            x={contextMenu.x}
            y={contextMenu.y}
            node={contextMenu.node}
            onClose={() => setContextMenu(null)}
            onExpand={(id) => handleNodeDoubleClick({ id })}
            onFocus={(id) => handleSearchSelect(id)}
          />
        )}
      </AnimatePresence>
      
    </div>
  );
}

// --- MOCK DATA ---
function mockGraphData(): GraphData {
  return {
    nodes: [
      { id: 'p101', label: 'Pump P-101', type: 'Pump', properties: { health: '91%', risk: 'Medium', area: 'Area A', status: 'Healthy' } },
      { id: 'v21', label: 'Valve V-21', type: 'Valve', properties: { health: '98%', risk: 'Low', area: 'Area A', status: 'Healthy' } },
      { id: 'tk01', label: 'Tank TK-01', type: 'Tank', properties: { health: '85%', risk: 'Medium', area: 'Area B', status: 'Warning' } },
      { id: 'm12', label: 'Motor M-12', type: 'Motor' },
      { id: 'pt101', label: 'PT-101', type: 'Sensor' },
      { id: 'pc101', label: 'PC-101', type: 'Controller' },
      { id: 'doc1', label: 'OEM Manual P-101', type: 'Document' },
      { id: 'sop1', label: 'Startup SOP (Area A)', type: 'SOP' },
      { id: 'maint1', label: 'Seal Replacement (WO-491)', type: 'Maintenance' },
      { id: 'insp1', label: 'Q3 Inspection', type: 'Inspection' },
      { id: 'pid1', label: 'P&ID A-100', type: 'P&ID' },
      { id: 'eng1', label: 'John Doe', type: 'People' },
      { id: 'areaA', label: 'Area A', type: 'Area' },
    ],
    edges: [
      { source: 'p101', target: 'v21', relation: 'CONNECTED_TO' },
      { source: 'p101', target: 'tk01', relation: 'CONNECTED_TO' },
      { source: 'm12', target: 'p101', relation: 'PART_OF' },
      { source: 'pt101', target: 'p101', relation: 'MONITORED_BY' },
      { source: 'pc101', target: 'pt101', relation: 'CONTROLS' },
      { source: 'doc1', target: 'p101', relation: 'REFERENCES' },
      { source: 'sop1', target: 'p101', relation: 'REFERENCES' },
      { source: 'maint1', target: 'p101', relation: 'MAINTAINED_BY' },
      { source: 'insp1', target: 'p101', relation: 'INSPECTED_BY' },
      { source: 'p101', target: 'pid1', relation: 'LOCATED_IN' },
      { source: 'eng1', target: 'maint1', relation: 'PERFORMED' },
      { source: 'p101', target: 'areaA', relation: 'LOCATED_IN' },
    ]
  };
}

function mockEntityDetails(nodeData: any): NodeDetails {
  return {
    docsCount: 12,
    maintCount: 36,
    inspCount: 18,
    woCount: 82,
    relatedAssets: [
      { id: 'v21', label: 'Valve V-21', type: 'Valve' },
      { id: 'tk01', label: 'Tank TK-01', type: 'Tank' },
      { id: 'm12', label: 'Motor M-12', type: 'Motor' }
    ],
    aiSummary: `${nodeData.rawLabel} has experienced two seal failures in the last year. Preventive maintenance is currently overdue based on runtime hours.`,
    recommendations: [
      "Inspect Bearings",
      "Lubricate Shaft",
      "Review OEM Manual"
    ]
  };
}
