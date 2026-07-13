"use client";

import React, { useEffect, useRef, useCallback } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { Loader2 } from "lucide-react";
import { GraphData } from "./types";

interface GraphCanvasProps {
  data: GraphData;
  filters: Record<string, boolean>;
  layoutName: string;
  loading: boolean;
  onNodeSelect: (nodeData: any) => void;
  onNodeDoubleClick: (nodeData: any) => void;
  onBackgroundClick: () => void;
  onContextMenu: (x: number, y: number, nodeData: any) => void;
  cyRefHook?: (cy: any) => void;
}

export default function GraphCanvas({
  data,
  filters,
  layoutName,
  loading,
  onNodeSelect,
  onNodeDoubleClick,
  onBackgroundClick,
  onContextMenu,
  cyRefHook
}: GraphCanvasProps) {
  const cyRef = useRef<any>(null);

  // Generate Cytoscape elements
  const elements = React.useMemo(() => {
    const cyElements: any[] = [];
    
    data.nodes.forEach(n => {
      if (filters[n.type] === false) return; // Filter out node

      // Icon mapping
      let icon = "🟢"; // default
      switch (n.type) {
        case "Equipment":
        case "Pump":
        case "Valve":
        case "Tank":
        case "Motor":
        case "Boiler":
        case "Compressor":
        case "Heat Exchanger": icon = "⚙️"; break;
        case "Controller":
        case "Instrument":
        case "Pressure Transmitter": icon = "🎛️"; break;
        case "Sensor": icon = "📡"; break;
        case "Document":
        case "Manual": icon = "📄"; break;
        case "Inspection": icon = "📋"; break;
        case "SOP": icon = "📘"; break;
        case "Maintenance": icon = "🔧"; break;
        case "P&ID": icon = "📐"; break;
        case "People": icon = "👤"; break;
        case "Area":
        case "Department": icon = "🏭"; break;
      }
      
      cyElements.push({
        data: {
          id: n.id,
          label: `${icon} ${n.label}`,
          rawLabel: n.label,
          type: n.type,
          properties: n.properties || {}
        }
      });
    });
    
    data.edges.forEach(e => {
      cyElements.push({
        data: {
          id: e.id || `${e.source}-${e.target}-${e.relation}`,
          source: e.source,
          target: e.target,
          label: e.relation,
          relation: e.relation
        }
      });
    });

    return cyElements;
  }, [data, filters]);

  // The layout will be handled directly via the layout prop on CytoscapeComponent

  const stylesheet: any[] = [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'text-valign': 'bottom' as const,
        'text-halign': 'center' as const,
        'text-margin-y': 6,
        'background-color': (ele: any) => {
          const type = ele.data('type');
          if (['Equipment', 'Pump', 'Valve', 'Tank', 'Motor', 'Boiler', 'Compressor', 'Heat Exchanger', 'Instrument'].includes(type)) return '#10b981'; // Green
          if (['Document', 'Manual'].includes(type)) return '#3b82f6'; // Blue
          if (['SOP'].includes(type)) return '#14b8a6'; // Teal
          if (['Maintenance'].includes(type)) return '#a855f7'; // Purple
          if (['Inspection'].includes(type)) return '#f97316'; // Orange
          if (['P&ID'].includes(type)) return '#06b6d4'; // Cyan
          if (['People'].includes(type)) return '#eab308'; // Yellow
          if (['Area', 'Department'].includes(type)) return '#065f46'; // Dark Green
          if (['Controller'].includes(type)) return '#ec4899'; // Pink
          if (['Sensor', 'Pressure Transmitter'].includes(type)) return '#ef4444'; // Red
          return '#6366f1';
        },
        'color': '#f8fafc',
        'font-size': '10px',
        'font-family': 'sans-serif',
        'width': 32,
        'height': 32,
        'border-width': 2,
        'border-color': '#fff',
        'border-opacity': 0.2,
        'text-outline-width': 1.5,
        'text-outline-color': '#0f172a'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': (ele: any) => {
          const rel = ele.data('relation');
          if (['CONNECTED_TO', 'PART_OF'].includes(rel)) return 3;
          if (['REFERENCES', 'REFERENCED_IN'].includes(rel)) return 1;
          return 2; // Medium line default
        },
        'line-color': (ele: any) => {
          const rel = ele.data('relation');
          if (rel === 'CONTROLS') return '#f97316'; // Orange
          if (rel === 'MONITORED_BY') return '#06b6d4'; // Cyan
          if (rel === 'MAINTAINED_BY') return '#a855f7'; // Purple
          if (rel === 'LOCATED_IN') return '#10b981'; // Green
          if (rel === 'INSPECTED_BY') return '#eab308'; // Yellow
          if (rel === 'USES') return '#ec4899'; // Pink
          return '#475569'; // Default Slate
        },
        'target-arrow-color': (ele: any) => {
          const rel = ele.data('relation');
          if (rel === 'CONTROLS') return '#f97316';
          if (rel === 'MONITORED_BY') return '#06b6d4';
          if (rel === 'MAINTAINED_BY') return '#a855f7';
          if (rel === 'LOCATED_IN') return '#10b981';
          if (rel === 'INSPECTED_BY') return '#eab308';
          if (rel === 'USES') return '#ec4899';
          return '#475569';
        },
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier' as const,
        'font-size': '8px',
        'color': '#cbd5e1',
        'text-outline-width': 1.5,
        'text-outline-color': '#0f172a',
        'text-rotation': 'autorotate' as const,
        'text-margin-y': -10,
        'opacity': 0.7,
      }
    },
    {
      selector: 'node.highlighted',
      style: {
        'width': 40,
        'height': 40,
        'border-width': 3,
        'border-color': '#fff',
        'border-opacity': 1,
        'underlay-color': '#818cf8',
        'underlay-padding': 8,
        'underlay-opacity': 0.8,
        'underlay-shape': 'ellipse'
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'label': 'data(label)',
        'opacity': 1,
        'width': 3,
        'z-index': 10
      }
    },
    {
      selector: 'node.dimmed',
      style: {
        'opacity': 0.15
      }
    },
    {
      selector: 'edge.dimmed',
      style: {
        'opacity': 0.1
      }
    }
  ];

  return (
    <div className="absolute inset-0 bg-[#0B0F19] overflow-hidden rounded-xl border border-slate-800">
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm rounded-xl">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        </div>
      )}
      <CytoscapeComponent
        elements={elements}
        style={{ width: '100%', height: '100%', display: 'block' }}
        stylesheet={stylesheet}
        layout={{ 
          name: layoutName, 
          animate: true,
          animationDuration: 500,
          nodeDimensionsIncludeLabels: true,
          padding: 50,
          fit: true
        }}
        maxZoom={4}
        minZoom={0.1}
        cy={(cy) => {
          if (cyRef.current !== cy) {
            cyRef.current = cy;
            if (cyRefHook) cyRefHook(cy);

            // Ensure canvas is properly sized on mount
            setTimeout(() => {
              cy.resize();
              cy.fit();
            }, 200);

            cy.on('tap', 'node', (e) => onNodeSelect(e.target.data()));
            cy.on('dblclick', 'node', (e) => onNodeDoubleClick(e.target.data()));
            cy.on('cxttap', 'node', (e) => onContextMenu(e.originalEvent.clientX, e.originalEvent.clientY, e.target.data()));
            
            // Edge hover labels
            cy.on('mouseover', 'edge', (e) => {
              e.target.style('label', e.target.data('label'));
              e.target.style('opacity', 1);
            });
            cy.on('mouseout', 'edge', (e) => {
              if (!e.target.hasClass('highlighted')) {
                e.target.style('label', '');
                e.target.style('opacity', 0.7);
              }
            });

            // Click background
            cy.on('tap', (e) => {
              if (e.target === cy) {
                onBackgroundClick();
              }
            });
          }
        }}
      />
    </div>
  );
}
