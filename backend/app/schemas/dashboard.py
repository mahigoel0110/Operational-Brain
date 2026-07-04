from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    organization_name: str
    total_workspaces: int
    total_documents: int
    total_chunks: int
    global_knowledge_score: int
    active_departments: list[str]
    ai_status: str