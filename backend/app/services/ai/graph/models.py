from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class GraphNode(BaseModel):
    """Represents a Node in the Knowledge Graph"""
    id: str = Field(..., description="Unique identifier for the node (usually normalized name)")
    name: str = Field(..., description="Display name of the entity")
    type: str = Field(..., description="Type of the entity (e.g., Equipment, Instrument)")
    document_id: Optional[str] = Field(None, description="Source document ID")
    chunk_id: Optional[str] = Field(None, description="Source chunk ID")
    page_number: Optional[int] = Field(None, description="Page number where entity was found")

class GraphRelationship(BaseModel):
    """Represents a Relationship (Edge) in the Knowledge Graph"""
    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    relation_type: str = Field(..., description="Type of relationship (e.g., MEASURES, CONTROLS)")
    confidence: float = Field(default=1.0, description="Confidence score of this extraction")
    document_id: Optional[str] = Field(None, description="Source document ID")
    chunk_id: Optional[str] = Field(None, description="Source chunk ID")

class ChunkGraph(BaseModel):
    """A subgraph extracted from a single chunk"""
    nodes: List[GraphNode] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)
