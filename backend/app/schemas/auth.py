from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    username: str
    default_currency: str

    class Config:
        from_attributes = True
