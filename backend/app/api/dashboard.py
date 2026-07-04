from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService
from app.models.organization import Organization

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    # In a real app we'd verify user belongs to org
    org = await Organization.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return await DashboardService.get_dashboard_summary(org_id)
