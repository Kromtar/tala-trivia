from fastapi import APIRouter, HTTPException, Depends, Form, status
from bcrypt import checkpw
from datetime import timedelta
from typing import List
from app.models.user import UserCreate, UserResponse
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_all_users,
    get_trivias_invitations_for_user,
    get_trivia_joined,
    get_trivias_played_by_user
)
from app.core.auth import create_access_token, admin_required, player_or_admin_required

# TODO: Pasar asegurando rutas

router = APIRouter()

@router.post(
    "/users",
    response_model=UserResponse,
    summary="Crear un nuevo Usuario",
    description="Este endpoint permite registrar un nuevo usuario en el sistema.",
    tags=["Users"],
)
async def create_user_endpoint(user: UserCreate):
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(user)

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="(Admin) Obtener todos los Usuarios",
    description="Devuelve una lista de todos los usuarios registrados.",
    tags=["Users"],
)
async def get_all_users_endpoint(current_user: dict = Depends(admin_required)):
    return await get_all_users()

# TODO: Falta modelo de respuesta, falta modelo de entrada
@router.post(
    "/users/login",
    summary="Login de usuario",
    description="Permite iniciar sesión con email y contraseña válidos.",
    tags=["Auth"],
    responses={
        400: {"description": "Credenciales inválidas"}
    },
)
async def login_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user or not checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token(
        # TODO: Validar uso de timedelta
        data={"sub": user.email, "role": user.role}, expires_delta=timedelta(minutes=300)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# TODO: Login de FastAPI Docs, cambiar ruta para que sea la misma que un login por API general
# TODO: Falta modelo de respuesta, falta modelo de entrada
@router.post(
    "/token",
    summary="Login de usuario Docs",
    tags=["Auth"]
)
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    user = await get_user_by_email(username)
    if not user or not checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=timedelta(minutes=300)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get(
    "/me/trivias_invitations",
    response_model=List[str],  # Devolver una lista de IDs
    summary="Obtener IDs de Trivias donde has sido invitado",
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
    response_model=dict,  # TODO: Añadir modelo
    summary="Obtener la ID de la Trivia en la que el usuario se ha unido",
    description="Obtiene la ID de la trivia donde el usuario ha aceptado una invitacion.\
        La respuesta indica si dicha Trivia aun se estan esperando jugadores o ya ha comenzado",
    tags=["Users"]
)
async def get_trivia_joined_endpoint(
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    trivia_id = await get_trivia_joined(current_user["email"])
    if not trivia_id:
        raise HTTPException(status_code=404, detail="No te has unido a ninguna Trivia.")
    return trivia_id

@router.get(
    "/me/trivias_played",
    response_model=List[str],
    summary="Obtener listado de IDs de Trivias ya jugadas por el usuario",
    tags=["Users"]
)
async def get_trivias_played(
    current_user: dict = Depends(player_or_admin_required),
):
    return await get_trivias_played_by_user(current_user["email"])
