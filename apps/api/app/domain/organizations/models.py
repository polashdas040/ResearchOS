from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class Organization(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str


class Membership(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole

