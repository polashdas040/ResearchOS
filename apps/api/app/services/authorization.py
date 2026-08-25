from uuid import UUID

from pydantic import BaseModel, ConfigDict

from apps.api.app.domain.organizations.models import OrganizationRole


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    organization_id: UUID
    roles: tuple[OrganizationRole, ...]


class AuthorizationService:
    def build_principal(
        self,
        user_id: UUID,
        organization_id: UUID,
        roles: list[OrganizationRole],
    ) -> Principal:
        return Principal(user_id=user_id, organization_id=organization_id, roles=tuple(roles))

    async def can_access_organization(
        self,
        principal: Principal,
        organization_id: UUID,
    ) -> bool:
        return principal.organization_id == organization_id

