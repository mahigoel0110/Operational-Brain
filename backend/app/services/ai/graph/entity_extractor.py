import logging
import spacy
from typing import List, Dict, Any

from app.services.ai.graph.ontology import ontology_manager
from app.services.ai.graph.prompts import ENTITY_EXTRACTION_PROMPT
from app.services.ai.graph.entity_resolver import entity_resolver
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        try:
            # Load spaCy model for general named entities
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model. Falling back entirely to regex/LLM. Run `python -m spacy download en_core_web_sm`: {e}")
            self.nlp = None

    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Hybrid extraction pipeline:
        1. Rule-based (Regex + Dictionary + Ontology)
        2. spaCy (General Named Entities)
        3. LLM (Fallback if rule-based yield poor results / as a safety net)
        """
        entities = []
        found_names = set()
        
        # 1. Regex & Ontology Matching (Fast & cheap)
        words = text.split()
        for word in words:
            clean_word = word.strip(".,;:'\"()[]{}")
            if not clean_word:
                continue
                
            entity_type = ontology_manager.get_entity_type(clean_word)
            if entity_type:
                normalized_name = entity_resolver.normalize_name(clean_word)
                if normalized_name not in found_names:
                    entities.append({"entity": normalized_name, "type": entity_type})
                    found_names.add(normalized_name)
                    
        # Multi-word dictionary matching (simple sliding window)
        # E.g. "Pressure Controller"
        if len(words) > 1:
            for i in range(len(words)-1):
                phrase = f"{words[i]} {words[i+1]}".strip(".,;:'\"()[]{}")
                entity_type = ontology_manager.get_entity_type(phrase)
                if entity_type:
                    normalized_name = entity_resolver.normalize_name(phrase)
                    if normalized_name not in found_names:
                        entities.append({"entity": normalized_name, "type": entity_type})
                        found_names.add(normalized_name)

        # 2. spaCy Extraction
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "FAC", "LOC"]:
                    entity_type = ontology_manager.get_entity_type(ent.text)
                    if not entity_type:
                        # Fallback for generic things that look like equipment/materials
                        entity_type = "Unknown"
                        
                    normalized_name = entity_resolver.normalize_name(ent.text)
                    if normalized_name and normalized_name not in found_names:
                        entities.append({"entity": normalized_name, "type": entity_type})
                        found_names.add(normalized_name)

        # 3. LLM Fallback
        # If we didn't find much, or if we want high recall, we can call the LLM.
        # To avoid calling it on every chunk, we use a simple heuristic:
        # If we found less than 2 entities, and the chunk is long enough, use the LLM.
        if len(entities) < 2 and len(text) > 50:
            try:
                llm_results = await LLMService.generate_json(
                    system_prompt=ENTITY_EXTRACTION_PROMPT.format(chunk=text),
                    user_prompt="Extract entities."
                )
                llm_entities = llm_results.get("entities", [])
                
                for item in llm_entities:
                    name = item.get("entity")
                    etype = item.get("type", "Unknown")
                    if name:
                        normalized = entity_resolver.normalize_name(name)
                        if normalized not in found_names:
                            entities.append({"entity": normalized, "type": etype})
                            found_names.add(normalized)
                            
            except Exception as e:
                logger.error(f"LLM Entity Extraction failed: {e}")

        # Post-process to dynamically update ontology with new findings
        for ent in entities:
            etype = ent["type"]
            name = ent["entity"]
            if etype and etype != "Unknown":
                ontology_manager.add_entity_alias(etype, name)

        return entities

entity_extractor = EntityExtractor()
