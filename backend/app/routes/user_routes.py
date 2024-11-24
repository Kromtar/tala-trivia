from fastapi import APIRouter, HTTPException, Depends, Form, status
from bcrypt import checkpw
from datetime import timedelta
from typing import List
from app.models.user import UserCreate, UserResponseInDB, UserToken
from app.models.trivia import TriviaStatus
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_all_users,
    get_trivias_invitations_for_user,
    get_trivia_joined,
    get_trivias_played_by_user
)
from app.core.auth import create_access_token, admin_required, player_or_admin_required
from app.core.constants import LOGIN_PATH

router = APIRouter()

@router.post(
    "/users",
    response_model=UserResponseInDB,
    status_code=201,
    summary="Crear un nuevo Usuario",
    description="Este endpoint permite registrar un nuevo usuario en el sistema. Dado el contexto\
        del proyecto, este endpoint no esta asegurado y es posible crear usuarios con rol\
        'player' y 'admin'",
    tags=["Users"],
)
async def create_user_endpoint(user: UserCreate):
    return await create_user(user)

@router.get(
    "/users",
    response_model=list[UserResponseInDB],
    summary="(Admin) Obtener todos los Usuarios",
    description="Devuelve una lista de todos los usuarios registrados.",
    tags=["Users"],
)
async def get_all_users_endpoint(current_user: dict = Depends(admin_required)):
    return await get_all_users()


@router.post(
    LOGIN_PATH,
    response_model=UserToken,
    summary="Login de usuario",
    description="Permite iniciar sesión con email y contraseña válidos.",
    tags=["Auth"]
)
async def login_for_access_token(
    username: str = Form(
        ...,
        description="La dirección de correo electrónico del usuario",
        example="guitarhero@email.com"
    ),
    password: str = Form(
        ...,
        description="La contraseña del usuario. Debe coincidir con la registrada en el sistema.",
        example="mypassword123"
    )
):
    user = await get_user_by_email(username, full=True)
    if not user or not checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=timedelta(minutes=300)
    )

    return UserToken(access_token=access_token, token_type="bearer")

@router.get(
    "/me/trivias_invitations",
    response_model=List[str],
    response_description="IDs de Trivias donde estoy invitado a participar",
    summary="Obtener IDs de Trivias donde has sido invitado. Solo puedes aceptar una invitación\
        de forma simultanea. Cuando todos los jugadores invitados a la Trivia acepten, esta inicia",
    tags=["Users"]
)
async def get_trivias_invitations_for_user_endpoint(
    current_user: dict = Depends(player_or_admin_required)
):
    trivia_ids = await get_trivias_invitations_for_user(current_user["email"])
    if not trivia_ids:
        raise HTTPException(status_code=404, detail="No estas invitado a ninguna Trivia")
    return trivia_ids

@router.get(
    "/me/trivia_joined",
    response_model=TriviaStatus,
    summary="Obtener la ID de la Trivia en la que el usuario se ha unido",
    description="Obtiene la ID de la trivia donde el usuario ha aceptado una invitación.\
        La respuesta indica si dicha Trivia aun se están esperando jugadores (waiting_start)\
            o ya ha comenzado (playing)",
    tags=["Users"]
)
async def get_trivia_joined_endpoint(
    current_user: dict = Depends(player_or_admin_required),
):
    trivia = await get_trivia_joined(current_user["email"])
    if trivia is False:
        raise HTTPException(status_code=404, detail="No te has unido a ninguna Trivia.")
    return trivia

@router.get(
    "/me/trivias_played",
    response_model=List[str],
    response_description="IDs de Trivias donde he jugado en el pasado.",
    summary="Obtener listado de IDs de Trivias ya jugadas por el usuario.",
    tags=["Users"]
)
async def get_trivias_played(
    current_user: dict = Depends(player_or_admin_required),
):
    olds_trivias = await get_trivias_played_by_user(current_user["email"])
    if len(olds_trivias) == 0:
        raise HTTPException(status_code=404, detail="Aun no has terminado de jugar ninguna Trivia")
    return olds_trivias
