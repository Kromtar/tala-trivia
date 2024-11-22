from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "player"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str

class UserFull(UserBase):
    id: str
    password: str
