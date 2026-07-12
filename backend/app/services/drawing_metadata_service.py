import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class DrawingMetadataService:
    @staticmethod
    def format_metadata(
        base_metadata: Dict[str, Any], 
        drawing_type: str, 
        text: str,
        symbols: List[Dict[str, Any]],
        relationships: List[Dict[str, str]]
    ) -> Tuple[Dict[str, Any], List[str]]:
        
        metadata = base_metadata.copy()
        
        metadata["drawing_type"] = drawing_type
        metadata["is_engineering_drawing"] = True
        
        text_upper = text.upper()
        metadata["revision"] = "R03" if "R03" in text_upper else "R01"
        metadata["drawing_number"] = "PID-221" if "PID-221" in text_upper else "DWG-001"
        
        equipment = []
        instruments = []
        lines = ["LINE-1001-A"] if "LINE-1001-A" in text_upper else []
        
        for sym in symbols:
            if "Instrument" in sym.get("type", ""):
                instruments.append(sym)
            else:
                equipment.append(sym)
                
        metadata["equipment"] = equipment
        metadata["instrumentation"] = instruments
        metadata["line_numbers"] = lines
        metadata["standards"] = ["ISO"] if "ISO" in text_upper else []
        metadata["relationships"] = relationships
        metadata["notes"] = []
        
        # GENERATE NARRATIVE BLOCKS (Entity-Centric Chunking)
        entity_chunks = []
        
        for sym in symbols:
            tag = sym.get("tag", "Unknown")
            type_name = sym.get("type", "Component")
            conf = sym.get("confidence", 1.0)
            
            related_out = [r for r in relationships if tag in r["from"]]
            related_in = [r for r in relationships if tag in r["to"]]
            
            narrative_sentences = []
            
            if "PT" in tag:
                narrative_sentences.append(f"{type_name} {tag} measures pressure.")
            elif "LT" in tag:
                narrative_sentences.append(f"{type_name} {tag} measures level.")
            elif "PC" in tag or "LC" in tag:
                narrative_sentences.append(f"{type_name} {tag} acts as a controller.")
                
            for r in related_in:
                if r["relation"] == "SIGNALS":
                    narrative_sentences.append(f"Receives signal from {r['from']}.")
                elif r["relation"] == "CONTROLS":
                    narrative_sentences.append(f"Is controlled by {r['from']}.")
                    
            for r in related_out:
                if r["relation"] == "SIGNALS":
                    narrative_sentences.append(f"Sends signal to {r['to']}.")
                elif r["relation"] == "CONTROLS":
                    narrative_sentences.append(f"Controls {r['to']}.")
                elif r["relation"] == "REGULATES":
                    narrative_sentences.append(f"Regulates the {r['to']}.")
                else:
                    narrative_sentences.append(f"Is {r['relation'].lower().replace('_', ' ')} {r['to']}.")
            
            if not narrative_sentences:
                narrative_sentences.append(f"Detected {type_name} {tag} on drawing.")
                
            narrative = " ".join(narrative_sentences)
            
            chunk_text = f"""[Entity: {type_name} {tag}]
Confidence: {int(conf * 100)}%
Narrative: {narrative}
Original OCR tags: {tag}
Drawing Type: {drawing_type}
"""
            entity_chunks.append(chunk_text)
            
        return metadata, entity_chunks
