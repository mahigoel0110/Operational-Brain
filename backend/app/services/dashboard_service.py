from app.schemas.dashboard import DashboardSummaryResponse
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.document import DocumentModel
from app.models.company_profile import CompanyProfile

class DashboardService:
    @staticmethod
    async def get_dashboard_summary(org_id: str) -> DashboardSummaryResponse:
        # Get Organization
        org = await Organization.get(org_id)
        org_name = org.name if org else "Unknown Organization"
        
        # Base stats
        workspaces = await Workspace.find(Workspace.organization_id == org_id).to_list()
        total_workspaces = len(workspaces)
        
        workspace_ids = [str(w.id) for w in workspaces]
        
        if not workspace_ids:
            return DashboardSummaryResponse(
                organization_name=org_name,
                total_workspaces=0,
                total_documents=0,
                total_chunks=0,
                global_knowledge_score=0,
                active_departments=[],
                ai_status="Awaiting Data"
            )
            
        docs = await DocumentModel.find({"workspace_id": {"$in": workspace_ids}}).to_list()
        total_documents = len(docs)
        total_chunks = sum(d.chunk_count for d in docs)
        
        # Integrate CompanyProfile insights
        profile = await CompanyProfile.find_one(CompanyProfile.organization_id == org_id)
        
        if profile:
            global_score = profile.ai_readiness_score
            departments = profile.departments
            
            if global_score > 80:
                ai_status = "Production Ready"
            elif global_score > 40:
                ai_status = "Learning in Progress"
            else:
                ai_status = "Gaps Detected - Interview Needed"
        else:
            global_score = 0
            departments = []
            ai_status = "Awaiting AI Synthesis"

        return DashboardSummaryResponse(
            organization_name=org_name,
            total_workspaces=total_workspaces,
            total_documents=total_documents,
            total_chunks=total_chunks,
            global_knowledge_score=global_score,
            active_departments=departments,
            ai_status=ai_status
        )