import logging
from typing import List, Dict, Any

from app.services.llm_service import LLMService
from app.services.ai.graph.prompts import QUERY_ENTITY_PROMPT
from app.services.ai.graph.entity_resolver import entity_resolver
from app.services.ai.graph.neo4j_client import neo4j_client
from app.services.ai.graph.graph_context_builder import graph_context_builder

logger = logging.getLogger(__name__)

class GraphRetriever:
    async def extract_query_entities(self, query: str) -> List[str]:
        """
        Uses LLM to identify potential entities from the user's query.
        """
        try:
            llm_results = await LLMService.generate_json(
                system_prompt=QUERY_ENTITY_PROMPT.format(query=query),
                user_prompt="Extract entities from the query."
            )
            entities = llm_results.get("entities", [])
            
            # Normalize them to match our IDs in Neo4j
            normalized = []
            for ent in entities:
                norm_name = entity_resolver.normalize_name(ent)
                if norm_name:
                    # We don't know the exact type, so we might need a more flexible ID match in Neo4j,
                    # or we can just search by name. For now, since IDs are typed, we can search by name in Neo4j.
                    # Wait, our Neo4j client's get_neighbors uses entity_ids. 
                    # Let's adjust get_neighbors or search by name.
                    normalized.append(norm_name)
                    
            return normalized
            
        except Exception as e:
            logger.error(f"Query entity extraction failed: {e}")
            return []

    async def get_graph_context(self, query: str, chunk_entities: List[str] = None) -> str:
        """
        Adaptive hop traversal based on query complexity.
        Returns a natural language paragraph describing the graph context.
        """
        query_entities = await self.extract_query_entities(query)
        
        all_entities = set(query_entities)
        if chunk_entities:
            all_entities.update([entity_resolver.normalize_name(e) for e in chunk_entities if e])
            
        if not all_entities:
            return ""
            
        # Determine hop count based on query
        # Very naive heuristic: more question words or complexity = more hops
        query_lower = query.lower()
        if "how" in query_lower and "process" in query_lower or "loop" in query_lower:
            hops = 3
        elif len(query.split()) > 7:
            hops = 2
        else:
            hops = 1
            
        # We need a new neo4j method to search by names instead of strict IDs
        # since query extraction doesn't yield entity types reliably.
        triples = await self._get_neighbors_by_name(list(all_entities), max_hops=hops)
        
        # Convert to text
        context_text = graph_context_builder.build_context(triples)
        return context_text
        
    async def _get_neighbors_by_name(self, names: List[str], max_hops: int) -> List[Dict[str, Any]]:
        """
        Helper method to search Neo4j by name instead of id.
        """
        if not neo4j_client.driver or not names:
            return []
            
        query = f"""
        MATCH p = (start:Entity)-[*1..{max_hops}]-(end:Entity)
        WHERE start.name IN $names
        // Filter out chunk and document nodes for context building
        AND NOT 'Chunk' IN labels(start) AND NOT 'Document' IN labels(start)
        AND NOT 'Chunk' IN labels(end) AND NOT 'Document' IN labels(end)
        RETURN [rel in relationships(p) | {{
            source: startNode(rel).id,
            source_name: startNode(rel).name,
            type: type(rel),
            target: endNode(rel).id,
            target_name: endNode(rel).name
        }}] AS rels
        """
        
        async with neo4j_client.driver.session() as session:
            try:
                result = await session.run(query, names=names)
                records = await result.data()
                
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
                logger.error(f"Error retrieving neighbors by name: {e}")
                return []

graph_retriever = GraphRetriever()
