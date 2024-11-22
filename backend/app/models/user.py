from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: str
    password: str
