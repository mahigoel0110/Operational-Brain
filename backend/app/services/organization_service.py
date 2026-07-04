from fastapi import HTTPException, status

from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate
)


class OrganizationService:

    @staticmethod
    async def create_organization(
        data: OrganizationCreate,
        owner_id: str
    ):

        organization = Organization(
            name=data.name,
            industry=data.industry,
            description=data.description,
            owner_id=owner_id,
            members=[owner_id]
        )

        await organization.insert()

        return organization

    @staticmethod
    async def get_all(user_id: str | None = None):
        if user_id:
            return await Organization.find({"members": user_id}).to_list()
        return await Organization.find_all().to_list()

    @staticmethod
    async def get_by_id(id: str, user_id: str | None = None):
        organization = await Organization.get(id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Enforce membership check if user_id is provided
        if user_id and user_id not in getattr(organization, "members", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )

        return organization

    @staticmethod
    async def update(
        id: str,
        data: OrganizationUpdate,
        user_id: str
    ):
        organization = await OrganizationService.get_by_id(id)

        # Enforce owner-only check
        if organization.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can perform this action"
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                organization,
                key,
                value
            )

        await organization.save()
        return organization

    @staticmethod
    async def delete(id: str, user_id: str):
        organization = await OrganizationService.get_by_id(id)

        # Enforce owner-only check
        if organization.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can perform this action"
            )

        await organization.delete()