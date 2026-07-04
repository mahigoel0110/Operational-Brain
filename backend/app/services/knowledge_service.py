import logging
from datetime import datetime, UTC
from app.models.company_profile import CompanyProfile
from app.models.interview import InterviewSession
from app.models.document import DocumentModel
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class KnowledgeService:

    @staticmethod
    async def synthesize_company_profile(org_id: str) -> CompanyProfile:
        """
        Gathers all interviews and documents for an organization and uses the LLM
        to synthesize a holistic Company Profile, detecting knowledge gaps.
        """
        # 1. Fetch raw data
        interviews = await InterviewSession.find(InterviewSession.organization_id == org_id).to_list()
        documents = await DocumentModel.find(DocumentModel.organization_id == org_id).to_list() if hasattr(DocumentModel, 'organization_id') else await DocumentModel.all().to_list() # Fallback if org_id not mapped strictly on doc
        
        # 2. Prepare context payload
        context_parts = []
        context_parts.append("=== EXTRACTED KNOWLEDGE ===")
        
        for doc in documents:
            dept = doc.department or "General"
            context_parts.append(f"Document: {doc.name} (Dept: {dept})")
            if doc.extracted_metadata:
                context_parts.append(f"  Summary: {doc.extracted_metadata.get('summary', 'N/A')}")
        
        context_parts.append("=== INTERVIEW INTELLIGENCE ===")
        for interview in interviews:
            if interview.status == "completed":
                context_parts.append(f"Department Interview: {interview.department}")
                for turn in interview.history:
                    if turn["role"] == "human":
                        context_parts.append(f"  Key Insight: {turn['content']}")
                        
        payload = "\n".join(context_parts)
        
        # 3. LLM JSON Extraction for Company Profile
        system_prompt = (
            "You are an Enterprise AI Architect synthesizing a Company Profile.\n"
            "Analyze the provided context (uploaded documents and human interview transcripts) to map out the organization.\n"
            "Return a JSON object matching this exact schema:\n"
            "{\n"
            "  'core_business': 'Summary of what the company does based on data',\n"
            "  'departments': ['List', 'of', 'detected', 'departments'],\n"
            "  'department_summaries': {'DeptName': '2 sentence summary of their operational role'},\n"
            "  'missing_policies': ['List of overarching policies that seem to be missing (e.g. HR Handbook)'],\n"
            "  'missing_critical_sops': ['List of specific critical SOPs that the interviews mentioned but are not uploaded'],\n"
            "  'ai_readiness_score': integer_from_0_to_100\n"
            "}\n"
            "The ai_readiness_score should reflect how complete their knowledge graph is. 100 means all departments have SOPs and no gaps are detected."
        )
        
        try:
            profile_data = await LLMService.generate_json(system_prompt, payload, temperature=0.2)
        except Exception as e:
            logger.error(f"Failed to synthesize company profile: {e}")
            profile_data = {
                "core_business": "Data extraction failed.",
                "departments": [],
                "department_summaries": {},
                "missing_policies": [],
                "missing_critical_sops": [],
                "ai_readiness_score": 0
            }
            
        # 4. Upsert Profile
        profile = await CompanyProfile.find_one(CompanyProfile.organization_id == org_id)
        if not profile:
            profile = CompanyProfile(organization_id=org_id)
            
        profile.core_business = profile_data.get("core_business", "")
        profile.departments = profile_data.get("departments", [])
        profile.department_summaries = profile_data.get("department_summaries", {})
        profile.missing_policies = profile_data.get("missing_policies", [])
        profile.missing_critical_sops = profile_data.get("missing_critical_sops", [])
        profile.ai_readiness_score = profile_data.get("ai_readiness_score", 0)
        profile.updated_at = datetime.now(UTC)
        
        await profile.save() if profile.id else await profile.insert()
        
        return profile
