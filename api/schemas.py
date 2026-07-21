from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class AdminDetailsSchema(BaseModel):
    id: int
    admin_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "Super Admin"
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminUserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime
    details: Optional[AdminDetailsSchema] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    access_token_expires_at: str
    refresh_token: str
    refresh_token_expires_at: str
    token_type: str = "bearer"
    user: AdminUserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    access_token_expires_at: str
    token_type: str = "bearer"
