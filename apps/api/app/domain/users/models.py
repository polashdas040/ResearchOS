from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    primary_organization_id: UUID

