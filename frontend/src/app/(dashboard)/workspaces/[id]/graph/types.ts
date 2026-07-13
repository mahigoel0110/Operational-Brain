export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  relation: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NodeDetails {
  docsCount: number;
  maintCount: number;
  inspCount: number;
  woCount: number;
  relatedAssets: Array<{ id: string; label: string; type: string }>;
  aiSummary: string;
  recommendations: string[];
}
