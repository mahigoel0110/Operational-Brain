"""
Core Industrial Ontology for Knowledge Graph

This module defines the foundational entity types, standard tags,
and regex rules for parsing industrial documents. 
It supports dynamic expansion when new entities are discovered during ingestion.
"""

import re
from typing import Dict, List, Optional

# Core Entity Types
ENTITY_TYPES = {
    "Instrument": [
        "PT", "LT", "TT", "FT", "PC", "LC", "TC", "FC",
        "Pressure Transmitter", "Level Transmitter",
        "Temperature Transmitter", "Flow Transmitter",
        "Pressure Controller", "Level Controller",
        "Temperature Controller", "Flow Controller"
    ],
    "Equipment": [
        "Separator", "Pump", "Compressor", "Tank",
        "Heat Exchanger", "Filter", "Vessel", "Heater"
    ],
    "Valve": [
        "PV", "LV", "XV", "TV", "FV", "Control Valve",
        "Relief Valve", "Blowdown Valve", "Block Valve"
    ],
    "ProcessVariable": [
        "Pressure", "Temperature", "Flow", "Level", "Viscosity", "Density"
    ],
    "Material": [
        "Oil", "Water", "Gas", "Steam", "Liquid", "Air", "Nitrogen"
    ],
    "Output": [
        "Oil Outlet", "Water Outlet", "Gas Outlet", "Vapor Outlet", "Drain"
    ],
    "InternalComponent": [
        "Demister Pad", "Weir", "Vortex Breaker", "Baffle", "Tray"
    ]
}

# Regex patterns for fast rule-based extraction
# Matches tags like P-101, P-102A, FV-201, PT-301A
TAG_REGEX = re.compile(r'\b([A-Z]{1,4}-?\d{2,4}[A-Z]?)\b')

class OntologyManager:
    def __init__(self):
        self.ontology = ENTITY_TYPES.copy()
        # Precompute a lookup dictionary for fast matching
        self._build_lookup()

    def _build_lookup(self):
        self.lookup: Dict[str, str] = {}
        for entity_type, aliases in self.ontology.items():
            for alias in aliases:
                self.lookup[alias.lower()] = entity_type

    def get_entity_type(self, entity_name: str) -> Optional[str]:
        """
        Returns the entity type if it exists in the ontology, else None.
        """
        # First check direct lookup
        if entity_name.lower() in self.lookup:
            return self.lookup[entity_name.lower()]
            
        # Check against Regex for generic tagging
        if TAG_REGEX.fullmatch(entity_name):
            # Try to infer based on prefix
            prefix = re.match(r'^([A-Z]+)', entity_name)
            if prefix:
                prefix_str = prefix.group(1)
                if prefix_str in ['PT', 'LT', 'TT', 'FT', 'PC', 'LC']:
                    return "Instrument"
                elif prefix_str in ['PV', 'LV', 'XV', 'FV', 'TV']:
                    return "Valve"
                elif prefix_str in ['P', 'C', 'V', 'T', 'E', 'F']:
                    return "Equipment"
                    
        return None

    def add_entity_alias(self, entity_type: str, alias: str):
        """
        Dynamically expands the ontology.
        """
        if entity_type not in self.ontology:
            self.ontology[entity_type] = []
        
        if alias not in self.ontology[entity_type]:
            self.ontology[entity_type].append(alias)
            self.lookup[alias.lower()] = entity_type

ontology_manager = OntologyManager()
