import re
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class MetadataExtractor:
    @classmethod
    def extract_metadata(cls, text: str, filename: str) -> Dict[str, Any]:
        """
        Extracts structured metadata from text.
        If OpenAI API key is present, uses LLM for high-fidelity structured extraction.
        Otherwise, falls back to rule-based regex extraction.
        """
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        
        # Try to use LLM if key is available
        if api_key:
            try:
                metadata = cls._extract_via_llm(text[:8000], filename, api_key)  # Limit text size to prevent token limits
                if metadata:
                    return metadata
            except Exception as e:
                logger.error(f"Failed to extract metadata via LLM: {e}. Falling back to heuristics.")

        # Fallback to heuristics
        return cls._extract_via_heuristics(text, filename)

    @classmethod
    def _extract_via_llm(cls, text: str, filename: str, api_key: str) -> Dict[str, Any] | None:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
You are an expert enterprise document classifier. Analyze the following document snippet from the file '{filename}' and extract key metadata.
Respond with a single JSON object. Do not include any markdown fences or explanation.

Expected JSON format:
{{
  "title": "Document Title",
  "department": "Department (e.g. Operations, Maintenance, Safety, HR, etc.)",
  "file_type": "PDF/DOCX/XLSX/etc.",
  "version": "1.0",
  "dates": ["list of key dates mentioned"],
  "people": ["list of key names"],
  "organizations": ["list of organization names"],
  "products": ["list of products"],
  "machines": ["list of machinery or equipment tags like Pump P-101"],
  "policies": ["list of company policies mentioned"],
  "sops": ["list of standard operating procedures mentioned"],
  "confidence_score": 0.85,
  "completeness_score": 0.90
}}

Snippet:
{text}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise data extractor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up any potential markdown formatting
        if content.startswith("```"):
            # strip markdown block
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        
        try:
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error parsing LLM response: {content}. Error: {e}")
            return None

    @classmethod
    def _extract_via_heuristics(cls, text: str, filename: str) -> Dict[str, Any]:
        """
        Rule-based heuristic extractor as a zero-cost local fallback.
        """
        # 1. Clean filename extension for default title
        base_name, ext = os.path.splitext(filename)
        title = base_name.replace("_", " ").replace("-", " ").title()

        # 2. Extract first few lines for potential title
        first_lines = [l.strip() for l in text.split("\n")[:5] if l.strip()]
        if first_lines and len(first_lines[0]) < 100:
            title = first_lines[0]

        # 3. Detect department
        department = "General"
        dept_lower = text.lower()
        if "maintenance" in dept_lower or "repair" in dept_lower or "calibration" in dept_lower:
            department = "Maintenance"
        elif "safety" in dept_lower or "hse" in dept_lower or "hazard" in dept_lower or "ppe" in dept_lower:
            department = "Safety"
        elif "compliance" in dept_lower or "audit" in dept_lower or "regulation" in dept_lower:
            department = "Compliance"
        elif "finance" in dept_lower or "invoice" in dept_lower or "billing" in dept_lower:
            department = "Finance"
        elif "operations" in dept_lower or "prod" in dept_lower or "operator" in dept_lower:
            department = "Operations"

        # 4. Extract version
        version = "1.0"
        version_match = re.search(r"(?:version|rev|revision|v)\s*[:\.]?\s*(\d+\.\d+)", text, re.IGNORECASE)
        if version_match:
            version = version_match.group(1)

        # 5. Extract dates
        # Matches YYYY-MM-DD or DD/MM/YYYY or standard dates
        dates = re.findall(r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})", text)
        dates = list(set(dates))[:5]  # Keep top 5 unique dates

        # 6. Extracted equipment tags / machines
        # Find tags like Pump P-101, Compressor C-202, Valve V-009, etc.
        machines = re.findall(r"\b(pump|compressor|valve|turbine|generator|reactor|boiler)\s+([a-zA-Z\d\-]{2,10})\b", text, re.IGNORECASE)
        machine_tags = [f"{m[0].title()} {m[1].upper()}" for m in machines]
        machine_tags = list(set(machine_tags))[:8]

        # 7. Extract people (heuristics - e.g., Approved by X, Prepared by Y)
        people = []
        people_matches = re.findall(r"(?:approved|prepared|reviewed|signed|author|engineer|manager)\s+by\s*[:\-]?\s*([a-zA-Z\s]{3,25})", text, re.IGNORECASE)
        for p in people_matches:
            name = p.strip().title()
            # Filter out generic titles
            if name not in ["The", "Operator", "Manager", "Engineer", "Supervisor", "Lead"]:
                people.append(name)
        people = list(set(people))[:5]

        # 8. Policies and SOPs indicators
        policies = []
        sops = []
        if "sop" in dept_lower or "standard operating procedure" in dept_lower:
            sops.append(title)
        if "policy" in dept_lower or "guideline" in dept_lower:
            policies.append(title)

        # Hackathon metrics calculation
        confidence_score = 0.65
        if machine_tags:
            confidence_score += 0.1
        if len(dates) > 0:
            confidence_score += 0.1
        if version != "1.0":
            confidence_score += 0.05
        confidence_score = min(0.95, confidence_score)

        completeness_score = min(0.9, 0.4 + (len(machine_tags)*0.1) + (len(dates)*0.1) + (len(people)*0.1))

        return {
            "title": title,
            "department": department,
            "file_type": ext[1:].upper(),
            "version": version,
            "dates": dates,
            "people": people,
            "organizations": ["OperationalBrain Corp"],
            "products": [],
            "machines": machine_tags,
            "policies": policies,
            "sops": sops,
            "confidence_score": round(confidence_score, 2),
            "completeness_score": round(completeness_score, 2),
        }
import os
