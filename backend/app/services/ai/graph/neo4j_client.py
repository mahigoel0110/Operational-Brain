import logging
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.core.config import settings
from app.services.ai.graph.models import ChunkGraph, GraphNode, GraphRelationship

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    async def connect(self):
        if not self.uri:
            logger.warning("Neo4j URI not configured. Graph features will be disabled.")
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connection
            await self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j.")
            await self._create_constraints()
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed.")

    async def _create_constraints(self):
        """Creates uniqueness constraints on the ID property to avoid duplicates."""
        if not self.driver:
            return
            
        queries = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]
        
        async with self.driver.session() as session:
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")

    async def insert_graph(self, chunk_graph: ChunkGraph):
        """
        Inserts nodes and relationships using MERGE to avoid duplicates.
        Handles soft-failure if neo4j is offline.
        """
        if not self.driver:
            return

        async with self.driver.session() as session:
            try:
                # 1. Insert Nodes
                for node in chunk_graph.nodes:
                    # Using parameterization for safety
                    query = f"""
                    MERGE (n:Entity {{id: $id}})
                    SET n.name = $name,
                        n.type = $type,
                        n.chunk_id = $chunk_id,
                        n.document_id = $document_id,
                        n.page_number = $page_number,
                        n:{node.type}
                    """
                    await session.run(
                        query,
                        id=node.id,
                        name=node.name,
                        type=node.type,
                        chunk_id=node.chunk_id,
                        document_id=node.document_id,
                        page_number=node.page_number
                    )

                # 2. Insert Relationships
                for rel in chunk_graph.relationships:
                    # Relationship types cannot be parameterized directly in Cypher,
                    # so we format it carefully (must be uppercase alphanumeric)
                    rel_type = "".join(c for c in rel.relation_type if c.isalnum() or c == "_").upper()
                    
                    query = f"""
                    MATCH (source:Entity {{id: $source_id}})
                    MATCH (target:Entity {{id: $target_id}})
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r.confidence = $confidence,
                        r.chunk_id = $chunk_id,
                        r.document_id = $document_id
                    """
                    await session.run(
                        query,
                        source_id=rel.source_id,
                        target_id=rel.target_id,
                        confidence=rel.confidence,
                        chunk_id=rel.chunk_id,
                        document_id=rel.document_id
                    )

            except Exception as e:
                logger.error(f"Error inserting graph data into Neo4j: {e}")

    async def get_neighbors(self, entity_ids: List[str], max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Traverses the graph up to max_hops from the given entity_ids.
        Returns a list of relationships (triples).
        """
        if not self.driver or not entity_ids:
            return []
            
        # Apoc is usually better for variable hops, but standard Cypher can do it too
        query = f"""
        MATCH p = (start:Entity)-[*1..{max_hops}]-(end:Entity)
        WHERE start.id IN $entity_ids
        RETURN [rel in relationships(p) | {{
            source: startNode(rel).id,
            source_name: startNode(rel).name,
            type: type(rel),
            target: endNode(rel).id,
            target_name: endNode(rel).name
        }}] AS rels
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, entity_ids=entity_ids)
                records = await result.data()
                
                # Flatten and deduplicate
                unique_triples = set()
                triples = []
                for record in records:
                    for rel in record.get("rels", []):
                        trip_tuple = (rel["source"], rel["type"], rel["target"])
                        if trip_tuple not in unique_triples:
                            unique_triples.add(trip_tuple)
                            triples.append(rel)
                            
                return triples
            except Exception as e:
                logger.error(f"Error retrieving neighbors from Neo4j: {e}")
                return []

    async def get_workspace_graph(self, limit: int = 500) -> Dict[str, Any]:
        """
        Retrieves a sub-graph of nodes and relationships up to a limit for initial visualization.
        In a real app, you would filter by document IDs belonging to a workspace, 
        but since the graph is shared, we'll fetch a limited random sub-graph.
        """
        if not self.driver:
            return {"nodes": [], "edges": []}
            
        # Cypher query to get nodes and edges
        query = f"""
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        LIMIT {limit}
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query)
                records = await result.data()
                
                nodes = {}
                edges = []
                
                for record in records:
                    n = record.get("n", {})
                    m = record.get("m", {})
                    r = record.get("r", {})
                    
                    if "id" in n and n["id"] not in nodes:
                        nodes[n["id"]] = {"id": n["id"], "label": n.get("name", n["id"]), "type": n.get("type", "Unknown")}
                    
                    if "id" in m and m["id"] not in nodes:
                        nodes[m["id"]] = {"id": m["id"], "label": m.get("name", m["id"]), "type": m.get("type", "Unknown")}
                    
                    edge_id = f"{n.get('id', '')}_{r[1]}_{m.get('id', '')}"
                    edges.append({
                        "id": edge_id,
                        "source": n.get("id", ""),
                        "target": m.get("id", ""),
                        "label": r[1]
                    })
                    
                return {
                    "nodes": list(nodes.values()),
                    "edges": edges
                }
            except Exception as e:
                logger.error(f"Error retrieving workspace graph: {e}")
                return {"nodes": [], "edges": []}
                
    async def search_graph(self, query_str: str) -> Dict[str, Any]:
        """
        Searches nodes by name (case-insensitive) and retrieves them with their 1-hop neighbors.
        """
        if not self.driver or not query_str:
            return {"nodes": [], "edges": []}
            
        query = """
        MATCH (n:Entity)
        WHERE toLower(n.name) CONTAINS toLower($query_str)
        OPTIONAL MATCH (n)-[r]-(m:Entity)
        RETURN n, r, m
        LIMIT 200
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, query_str=query_str)
                records = await result.data()
                
                nodes = {}
                edges = []
                
                for record in records:
                    n = record.get("n", {})
                    if "id" in n and n["id"] not in nodes:
                        nodes[n["id"]] = {"id": n["id"], "label": n.get("name", n["id"]), "type": n.get("type", "Unknown")}
                        
                    m = record.get("m")
                    r = record.get("r")
                    
                    if m and r:
                        if "id" in m and m["id"] not in nodes:
                            nodes[m["id"]] = {"id": m["id"], "label": m.get("name", m["id"]), "type": m.get("type", "Unknown")}
                        
                        # Determine edge direction
                        # A standard neo4j python driver relationship is a tuple: (start_node, type, end_node)
                        # We just need to determine source and target
                        rel_type = r[1]
                        
                        # Actually for OPTIONAL MATCH (n)-[r]-(m), the direction could be either way.
                        # We can extract start and end nodes from the relationship object, but since 
                        # the neo4j library returns it as (start_node_properties, type, end_node_properties) in some contexts,
                        # or as a Relationship object.
                        # For simplicity, we just use the `r` relationship object itself.
                        # Wait, when doing `await result.data()`, it serializes nodes/relationships to dicts.
                        # Relationships are usually tuple (start_node_id, type, end_node_id) in dict serialization, but let's be careful.
                        edges.append({
                            "id": f"edge_{len(edges)}",
                            "source": r[0].get("id", "") if isinstance(r[0], dict) else n.get("id"),
                            "target": r[2].get("id", "") if isinstance(r[2], dict) else m.get("id"),
                            "label": r[1]
                        })
                        
                return {
                    "nodes": list(nodes.values()),
                    "edges": edges
                }
            except Exception as e:
                logger.error(f"Error searching graph: {e}")
                return {"nodes": [], "edges": []}
                
    async def get_entity_details(self, entity_id: str) -> Dict[str, Any]:
        """
        Gets full details for an entity, including its 1-hop neighbors and chunks.
        """
        if not self.driver:
            return {}
            
        query = """
        MATCH (n:Entity {id: $entity_id})
        OPTIONAL MATCH (n)-[r]->(m:Entity)
        OPTIONAL MATCH (k:Entity)-[r2]->(n)
        RETURN n, collect(DISTINCT {type: r[1], target: m.id, target_name: m.name, direction: "outgoing", chunk_id: r.chunk_id}) as outgoing,
               collect(DISTINCT {type: r2[1], source: k.id, source_name: k.name, direction: "incoming", chunk_id: r2.chunk_id}) as incoming
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, entity_id=entity_id)
                record = await result.single()
                
                if not record or not record.get("n"):
                    return {}
                    
                n = record["n"]
                outgoing = [rel for rel in record.get("outgoing", []) if rel.get("target")]
                incoming = [rel for rel in record.get("incoming", []) if rel.get("source")]
                
                return {
                    "id": n.get("id"),
                    "name": n.get("name"),
                    "type": n.get("type"),
                    "chunk_id": n.get("chunk_id"),
                    "document_id": n.get("document_id"),
                    "page_number": n.get("page_number"),
                    "relationships": outgoing + incoming
                }
            except Exception as e:
                logger.error(f"Error retrieving entity details: {e}")
                return {}

neo4j_client = Neo4jClient()
