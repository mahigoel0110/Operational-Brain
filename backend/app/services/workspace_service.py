from fastapi import HTTPException, status

from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate
)


class WorkspaceService:

    @staticmethod
    async def create(
        data: WorkspaceCreate,
        created_by: str
    ):

        workspace = Workspace(
            organization_id=data.organization_id,
            name=data.name,
            description=data.description,
            workspace_type=data.workspace_type,
            created_by=created_by
        )

        await workspace.insert()

        return workspace

    @staticmethod
    async def get_all(organization_id: str | None = None):
        if organization_id:
            return await Workspace.find(Workspace.organization_id == organization_id).to_list()
        return await Workspace.find_all().to_list()

    @staticmethod
    async def get_by_id(id: str):

        workspace = await Workspace.get(id)

        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        return workspace

    @staticmethod
    async def get_workspace_details(id: str):

        return await WorkspaceService.get_by_id(id)

    @staticmethod
    async def update(
        id: str,
        data: WorkspaceUpdate
    ):

        workspace = await WorkspaceService.get_by_id(id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                workspace,
                key,
                value
            )

        await workspace.save()

        return workspace

    @staticmethod
    async def delete(id: str):

        workspace = await WorkspaceService.get_by_id(id)

        await workspace.delete()

        return {
            "message": "Workspace deleted successfully"
        }