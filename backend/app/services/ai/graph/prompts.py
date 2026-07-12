"""
Prompts for Knowledge Graph Extraction
"""

ENTITY_EXTRACTION_PROMPT = """
You are an expert industrial knowledge extraction AI.
Extract named entities from the following text chunk. Focus ONLY on industrial entities such as:
Equipment, Instruments, Valves, Process Variables, Materials, and Outputs.

Return the result as a strict JSON object with a single key "entities" containing a list of objects, each with:
- "entity": The name or tag of the entity.
- "type": The category (e.g., Equipment, Instrument, Valve, ProcessVariable).

Text Chunk:
"{chunk}"

JSON Output:
"""

RELATION_EXTRACTION_PROMPT = """
You are an expert industrial knowledge extraction AI.
Given the following text chunk and the list of entities found within it,
identify structural relationships between these entities.

Common relation types:
MEASURES, CONTROLS, SENDS_SIGNAL_TO, REGULATES, CONNECTED_TO, LOCATED_ON, INSTALLED_ON, CONTAINS, SEPARATES, REMOVES, FLOWS_TO, USES, INPUT_TO, OUTPUT_TO, MONITORS, ACTIVATES, PART_OF.

Return the result as a strict JSON object with a single key "relations" containing a list of objects (triples), each with:
- "source": The name of the subject entity.
- "relation": The relation type (in uppercase).
- "target": The name of the object entity.

Entities:
{entities}

Text Chunk:
"{chunk}"

JSON Output:
"""

QUERY_ENTITY_PROMPT = """
Identify industrial entities (Equipment, Instruments, etc.) from the user's query to help search the knowledge graph.
Return a strict JSON object with a single key "entities" containing a list of strings representing the entity names/tags.

User Query:
"{query}"

JSON Output:
"""

GRAPH_SUMMARY_PROMPT = """
Summarize the following graph relationships into natural language sentences.
You are given a list of triples. Write a concise, readable paragraph describing how these entities interact.

Graph Triples:
{triples}

Natural Language Summary:
"""
