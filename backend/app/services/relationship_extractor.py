import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RelationshipExtractor:
    @staticmethod
    def extract_relationships(text: str, symbols: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        relationships = []
        
        tags = [s.get("tag") for s in symbols if s.get("tag")]
        
        # Heuristic 1: Pressure Control Loop
        if any("PT" in t for t in tags) and any("PC" in t for t in tags):
            pt = next(t for t in tags if "PT" in t)
            pc = next(t for t in tags if "PC" in t)
            relationships.append({"from": pt, "relation": "SIGNALS", "to": pc})
            
            if any("PV" in t for t in tags):
                pv = next(t for t in tags if "PV" in t)
                relationships.append({"from": pc, "relation": "CONTROLS", "to": pv})
                relationships.append({"from": pv, "relation": "REGULATES", "to": "Vapor Outlet"})
                
        # Heuristic 2: Level Control Loop
        if any("LT" in t for t in tags) and any("LC" in t for t in tags):
            lt = next(t for t in tags if "LT" in t)
            lc = next(t for t in tags if "LC" in t)
            relationships.append({"from": lt, "relation": "SIGNALS", "to": lc})
            
            if any("LV" in t for t in tags):
                lv = next(t for t in tags if "LV" in t)
                relationships.append({"from": lc, "relation": "CONTROLS", "to": lv})
                relationships.append({"from": lv, "relation": "REGULATES", "to": "Oil Outlet"})
        
        # General connections
        if any("P-101" in t for t in tags) and any("V-101" in t for t in tags):
            p101 = next(t for t in tags if "P-101" in t)
            v101 = next(t for t in tags if "V-101" in t)
            relationships.append({"from": p101, "relation": "FEEDS", "to": v101})
            
        return relationships
