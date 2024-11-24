from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from app.core.constants import ROLES

class UserBase(BaseModel):
    name: str = Field(
        ...,
        description="El nombre completo del usuario.",
        example="GuitarHero"
    )
    email: EmailStr = Field(
        ...,
        description="La dirección de correo electrónico del usuario.",
        example="guitarhero@email.com"
    )
    role: Optional[Literal[tuple(ROLES)]] = Field(
        "player",
        description="El rol del usuario dentro de la aplicación. Puede ser 'player' (jugador)\
             o 'admin' (administrador). El valor por defecto es 'player'.",
        example="player"
    )


""" Dado el contexto del proyecto, no aplicamos ninguna restricción en complejidad de password"""
class UserCreate(UserBase):
    password: str = Field(
        ...,
        description="La contraseña del usuario.",
        example="mypassword123"
    )

class UserResponseInDB(UserBase):
    id: str = Field(
        ...,
        description="El identificador único del usuario.",
        example="60b5fbd5e4b0f35c7b6b8e5c"
    )

class UserFull(UserBase):
    id: str = Field(
        ...,
        description="El identificador único del usuario.",
        example="60b5fbd5e4b0f35c7b6b8e5c"
    )
    password: str = Field(
        ...,
        description="La contraseña con hash",
    )

class UserToken(BaseModel):
    access_token: str = Field(
        ...,
        description="Token de acceso",
    )
    token_type: str = Field(
        ...,
        description="Tipo de Token",
    )
