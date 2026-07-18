from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List

from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.services.maintenance_service import MaintenanceService

router = APIRouter()

async def _validate_workspace(workspace_id: str) -> Workspace:
    ws = await Workspace.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws

@router.get("/equipment", response_model=List[Dict[str, str]])
async def get_equipment(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Returns a distinct list of equipment found in the workspace documents.
    """
    await _validate_workspace(workspace_id)
    try:
        equipment_list = await MaintenanceService.get_equipment_list(workspace_id)
        return equipment_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligence", response_model=Dict[str, Any])
async def get_maintenance_intelligence(
    workspace_id: str,
    equipment_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Generates a full AI Maintenance Report for the given equipment.
    """
    await _validate_workspace(workspace_id)
    if not equipment_name:
        raise HTTPException(status_code=400, detail="Equipment name is required")
        
    try:
        intelligence = await MaintenanceService.generate_maintenance_intelligence(
            workspace_id=workspace_id,
            equipment_name=equipment_name
        )
        return intelligence
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
