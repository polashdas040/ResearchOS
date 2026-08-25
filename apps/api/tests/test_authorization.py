from uuid import uuid4

import pytest

from apps.api.app.domain.organizations.models import OrganizationRole
from apps.api.app.services.authorization import AuthorizationService


@pytest.mark.asyncio
async def test_authorization_blocks_cross_organization_access() -> None:
    service = AuthorizationService()

    principal = service.build_principal(
        user_id=uuid4(),
        organization_id=uuid4(),
        roles=[OrganizationRole.RESEARCHER],
    )

    assert await service.can_access_organization(principal, principal.organization_id)
    assert not await service.can_access_organization(principal, uuid4())
