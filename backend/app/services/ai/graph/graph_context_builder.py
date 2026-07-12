from typing import List, Dict, Any

class GraphContextBuilder:
    """
    Converts raw graph triples into natural language sentences
    so that the LLM can understand them better than just raw JSON.
    """
    
    def __init__(self):
        # A simple template map for known relation types
        self.templates = {
            "MEASURES": "{source} measures {target}.",
            "CONTROLS": "{source} controls {target}.",
            "SENDS_SIGNAL_TO": "{source} sends a signal to {target}.",
            "REGULATES": "{source} regulates the {target}.",
            "CONNECTED_TO": "{source} is connected to {target}.",
            "LOCATED_ON": "{source} is located on {target}.",
            "INSTALLED_ON": "{source} is installed on {target}.",
            "CONTAINS": "{source} contains {target}.",
            "SEPARATES": "{source} separates {target}.",
            "REMOVES": "{source} removes {target}.",
            "FLOWS_TO": "{source} flows to {target}.",
            "USES": "{source} uses {target}.",
            "INPUT_TO": "{source} is an input to {target}.",
            "OUTPUT_TO": "{source} is an output to {target}.",
            "MONITORS": "{source} monitors {target}.",
            "ACTIVATES": "{source} activates {target}.",
            "PART_OF": "{source} is part of {target}.",
            "MENTIONS": "{source} is mentioned in {target}.",
            "BELONGS_TO": "{source} belongs to {target}."
        }

    def build_context(self, triples: List[Dict[str, Any]]) -> str:
        """
        Takes a list of triples and converts them to sentences.
        Triples should have 'source_name', 'type', 'target_name'.
        """
        if not triples:
            return ""
            
        sentences = []
        for rel in triples:
            source = rel.get("source_name", "Unknown Source")
            target = rel.get("target_name", "Unknown Target")
            rel_type = rel.get("type", "")
            
            if rel_type in self.templates:
                sentence = self.templates[rel_type].format(source=source, target=target)
            else:
                # Generic fallback
                human_rel = rel_type.replace("_", " ").lower()
                sentence = f"{source} {human_rel} {target}."
                
            sentences.append(sentence)
            
        return " ".join(sentences)

graph_context_builder = GraphContextBuilder()
