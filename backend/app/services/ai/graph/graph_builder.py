import logging
from typing import List, Dict, Any

from app.services.ai.graph.models import ChunkGraph, GraphNode, GraphRelationship
from app.services.ai.graph.entity_extractor import entity_extractor
from app.services.ai.graph.relation_extractor import relation_extractor
from app.services.ai.graph.entity_resolver import entity_resolver
from app.services.ai.graph.neo4j_client import neo4j_client
from app.services.ai.graph.entity_cache import entity_cache

logger = logging.getLogger(__name__)

class GraphBuilder:
    async def build_from_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_id: str, 
        document_name: str
    ):
        """
        Processes a list of chunks, extracts entities and relationships, 
        and inserts them into Neo4j.
        """
        for index, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if not text:
                continue
                
            # We can use the chunk's position or a hash for chunk_id if not provided
            chunk_id = chunk.get("id") or f"{document_id}_chunk_{index}"
            
            # Use cache to avoid reprocessing identical text
            cache_key = f"chunk_extract_{hash(text)}"
            if entity_cache.has(cache_key):
                continue
                
            try:
                # 1. Extract Entities
                extracted_entities = await entity_extractor.extract_entities(text)
                
                # Deduplicate entities for this chunk
                unique_nodes = {}
                for ent in extracted_entities:
                    norm_name = ent["entity"]
                    etype = ent["type"]
                    node_id = entity_resolver.generate_id(norm_name, etype)
                    
                    if node_id not in unique_nodes:
                        unique_nodes[node_id] = GraphNode(
                            id=node_id,
                            name=norm_name,
                            type=etype,
                            document_id=document_id,
                            chunk_id=chunk_id
                        )
                
                # 2. Extract Relationships
                extracted_relations = []
                if len(unique_nodes) > 1:
                    raw_relations = await relation_extractor.extract_relations(text, extracted_entities)
                    
                    # Deduplicate relations
                    unique_rels = set()
                    for rel in raw_relations:
                        # Find the corresponding node IDs
                        source_id = None
                        target_id = None
                        
                        # Very simple resolution back to our nodes
                        for node in unique_nodes.values():
                            if node.name == rel["source"]:
                                source_id = node.id
                            if node.name == rel["target"]:
                                target_id = node.id
                                
                        if source_id and target_id:
                            rel_type = rel["relation"]
                            rel_tuple = (source_id, rel_type, target_id)
                            
                            if rel_tuple not in unique_rels:
                                unique_rels.add(rel_tuple)
                                extracted_relations.append(GraphRelationship(
                                    source_id=source_id,
                                    target_id=target_id,
                                    relation_type=rel_type,
                                    confidence=1.0, # LLM confidence could be parsed here
                                    document_id=document_id,
                                    chunk_id=chunk_id
                                ))
                
                # 3. Create Document and Chunk nodes implicitly via relationships
                # We add standard relationships linking the chunk to the document,
                # and the entities to the chunk.
                doc_node_id = f"doc_{document_id}"
                chunk_node_id = f"chunk_{chunk_id}"
                
                # Add Document and Chunk nodes
                unique_nodes[doc_node_id] = GraphNode(
                    id=doc_node_id, name=document_name, type="Document", document_id=document_id
                )
                unique_nodes[chunk_node_id] = GraphNode(
                    id=chunk_node_id, name=f"Chunk {index}", type="Chunk", document_id=document_id, chunk_id=chunk_id
                )
                
                # Link Chunk to Document
                extracted_relations.append(GraphRelationship(
                    source_id=chunk_node_id,
                    target_id=doc_node_id,
                    relation_type="BELONGS_TO",
                    document_id=document_id,
                    chunk_id=chunk_id
                ))
                
                # Link Entities to Chunk
                for node_id, node in unique_nodes.items():
                    if node.type not in ["Document", "Chunk"]:
                        extracted_relations.append(GraphRelationship(
                            source_id=node_id,
                            target_id=chunk_node_id,
                            relation_type="MENTIONS",
                            document_id=document_id,
                            chunk_id=chunk_id
                        ))
                
                # 4. Insert into Neo4j
                chunk_graph = ChunkGraph(
                    nodes=list(unique_nodes.values()),
                    relationships=extracted_relations
                )
                
                await neo4j_client.insert_graph(chunk_graph)
                
                # Mark as processed
                entity_cache.set(cache_key, True)
                
            except Exception as e:
                logger.error(f"Error building graph for chunk {chunk_id}: {e}")

graph_builder = GraphBuilder()
