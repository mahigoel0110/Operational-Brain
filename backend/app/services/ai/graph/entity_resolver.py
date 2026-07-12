import re
from typing import Optional

class EntityResolver:
    """
    Normalizes and deduplicates entity names.
    For example: "Pressure Controller", "PC", "Pressure Ctrl" -> "Pressure Controller".
    """
    def __init__(self):
        # A simple alias map. In production, this might be loaded from a DB or Ontology.
        self.alias_map = {
            "pc": "Pressure Controller",
            "pressure ctrl": "Pressure Controller",
            "pt": "Pressure Transmitter",
            "press transmitter": "Pressure Transmitter",
            "lt": "Level Transmitter",
            "lc": "Level Controller",
            "pv": "Pressure Valve",
            "lv": "Level Valve",
            "tt": "Temperature Transmitter",
            "tc": "Temperature Controller",
            "ft": "Flow Transmitter",
            "fc": "Flow Controller",
            "temp": "Temperature",
            "press": "Pressure"
        }
        
    def normalize_name(self, raw_name: str) -> str:
        """
        Cleans the string and resolves aliases.
        """
        if not raw_name:
            return ""
            
        # Clean up whitespace and punctuation
        name = raw_name.strip()
        name = re.sub(r'\s+', ' ', name)
        
        # Check alias map
        lower_name = name.lower()
        if lower_name in self.alias_map:
            return self.alias_map[lower_name]
            
        # If it matches a strict tag (e.g., P-101), usually we uppercase it to normalize
        if re.fullmatch(r'[A-Za-z]{1,4}-?\d{2,4}[A-Za-z]?', name):
            return name.upper()
            
        # Otherwise, title case looks better for Graph Nodes
        if len(name) > 3 and name.islower():
            return name.title()
            
        return name

    def generate_id(self, normalized_name: str, entity_type: str) -> str:
        """
        Generates a consistent ID for the graph node.
        """
        base = re.sub(r'[^a-zA-Z0-9]', '_', normalized_name).lower()
        type_str = entity_type.lower() if entity_type else "unknown"
        return f"{type_str}_{base}"

entity_resolver = EntityResolver()
