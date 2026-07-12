import json
import logging
from typing import List, Dict, Any

from app.services.llm_service import LLMService
from app.services.ai.graph.prompts import RELATION_EXTRACTION_PROMPT
from app.services.ai.graph.entity_resolver import entity_resolver

logger = logging.getLogger(__name__)

class RelationExtractor:
    
    async def extract_relations(self, text: str, entities: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Extracts structural relationships (triples) from the text chunk based on the identified entities.
        Returns a list of dicts: [{"source": "...", "relation": "...", "target": "..."}]
        """
        if len(entities) < 2:
            return []
            
        entity_names = [e["entity"] for e in entities]
        entity_str = json.dumps(entity_names, indent=2)
        
        system_prompt = RELATION_EXTRACTION_PROMPT.format(
            entities=entity_str,
            chunk=text
        )
        
        try:
            llm_results = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt="Extract relations as instructed."
            )
            
            raw_relations = llm_results.get("relations", [])
            valid_relations = []
            
            for rel in raw_relations:
                source = rel.get("source")
                relation_type = rel.get("relation")
                target = rel.get("target")
                
                if source and relation_type and target:
                    # Normalize source and target to match our entity ids
                    norm_source = entity_resolver.normalize_name(source)
                    norm_target = entity_resolver.normalize_name(target)
                    
                    if norm_source and norm_target:
                        valid_relations.append({
                            "source": norm_source,
                            "relation": str(relation_type).upper().replace(" ", "_"),
                            "target": norm_target
                        })
                        
            return valid_relations
            
        except Exception as e:
            logger.error(f"Relation Extraction failed: {e}")
            return []

relation_extractor = RelationExtractor()
