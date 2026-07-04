from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user

from app.models.user import User

from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)

from app.services.organization_service import (
    OrganizationService
)

router = APIRouter()


@router.post(
    "/",
    response_model=OrganizationResponse
)
async def create(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user)
):

    organization = await OrganizationService.create_organization(
        data,
        str(current_user.id)
    )

    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        industry=organization.industry,
        description=organization.description
    )


@router.get("/", response_model=list[OrganizationResponse])
async def get_all(current_user: User = Depends(get_current_user)):

    organizations = await OrganizationService.get_all(str(current_user.id))
    return [
        OrganizationResponse(
            id=str(org.id),
            name=org.name,
            industry=org.industry,
            description=org.description
        )
        for org in organizations
    ]


@router.get("/{id}")
async def get_one(id: str, current_user: User = Depends(get_current_user)):

    return await OrganizationService.get_by_id(id, str(current_user.id))


@router.put("/{id}")
async def update(
    id: str,
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_user)
):

    return await OrganizationService.update(
        id,
        data,
        str(current_user.id)
    )


@router.delete("/{id}")
async def delete(id: str, current_user: User = Depends(get_current_user)):

    await OrganizationService.delete(id, str(current_user.id))

    return {
        "message": "Organization deleted."
    }