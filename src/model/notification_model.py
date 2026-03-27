from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailNotification(BaseModel):
    from_email: EmailStr
    to: list[EmailStr]
    cc: Optional[list[EmailStr]] = Field(default_factory=list)
    bcc: Optional[list[EmailStr]] = Field(default_factory=list)
    subject: str
    body: str


class TeamsNotification(BaseModel):
    title: str
    body: str
