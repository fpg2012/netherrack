from datetime import datetime

from pydantic import BaseModel, Field


class InviteCreate(BaseModel):
    expires_in_days: int | None = Field(default=7, ge=1, le=90)
    note: str | None = Field(default=None, max_length=100)


class InviteCreated(BaseModel):
    id: int
    code: str
    expires_at: datetime | None
    note: str | None = None


class InviteOut(BaseModel):
    id: int
    hint: str
    note: str | None = None
    status: str
    created_at: datetime
    expires_at: datetime | None
    used_at: datetime | None
    used_by: str | None = None
    created_by: str | None = None
    revoked_at: datetime | None
