import asyncio
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user

from app.models.user import User

from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse
)

from app.services.workspace_service import (
    WorkspaceService
)
from app.services.company_profile_service import CompanyProfileService

router = APIRouter()


@router.post(
    "/",
    response_model=WorkspaceResponse
)
async def create(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user)
):

    workspace = await WorkspaceService.create(
        data,
        str(current_user.id)
    )

    # Immediately seed initial CompanyProfile in background (no await — non-blocking)
    asyncio.create_task(
        CompanyProfileService.seed_from_workspace(
            workspace_id=str(workspace.id),
            organization_id=workspace.organization_id,
            name=workspace.name,
            description=workspace.description
        )
    )

    return WorkspaceResponse(
        id=str(workspace.id),
        organization_id=workspace.organization_id,
        name=workspace.name,
        description=workspace.description,
        workspace_type=workspace.workspace_type,
        created_by=workspace.created_by,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at
    )


@router.get("/", response_model=list[WorkspaceResponse])
async def get_all(
    organization_id: str | None = None,
    current_user: User = Depends(get_current_user)
):

    workspaces = await WorkspaceService.get_all(organization_id)
    return [
        WorkspaceResponse(
            id=str(ws.id),
            organization_id=ws.organization_id,
            name=ws.name,
            description=ws.description,
            workspace_type=ws.workspace_type,
            created_by=ws.created_by,
            created_at=ws.created_at,
            updated_at=ws.updated_at
        )
        for ws in workspaces
    ]


@router.get(
    "/{id}",
    response_model=WorkspaceResponse
)
async def get_workspace(id: str):

    workspace = await WorkspaceService.get_workspace_details(id)

    return WorkspaceResponse(

        id=str(workspace.id),

        organization_id=workspace.organization_id,

        name=workspace.name,

        description=workspace.description,

        workspace_type=workspace.workspace_type,

        created_by=workspace.created_by,

        created_at=workspace.created_at,

        updated_at=workspace.updated_at
    )

@router.put("/{id}")
async def update(
    id: str,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user)
):

    return await WorkspaceService.update(
        id,
        data
    )


@router.delete("/{id}")
async def delete(
    id: str,
    current_user: User = Depends(get_current_user)
):

    await WorkspaceService.delete(id)

    return {
        "message": "Workspace deleted."
    }