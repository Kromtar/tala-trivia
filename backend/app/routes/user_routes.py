from fastapi import APIRouter, HTTPException, Depends, Form, status
from bcrypt import checkpw
from datetime import timedelta
from app.models.user import UserCreate, UserResponse
from app.services.user_service import create_user, get_user_by_email, get_all_users
from app.core.auth import create_access_token, get_current_user

router = APIRouter()

@router.post(
    "/users",
    response_model=UserResponse,
    summary="Crear un nuevo usuario",
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
    summary="Obtener todos los usuarios",
    description="Devuelve una lista de todos los usuarios registrados.",
    tags=["Users"],
)
async def get_all_users_endpoint():
    return await get_all_users()

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
        data={"sub": user.name}, expires_delta=timedelta(minutes=300)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# TODO: Login de FastAPI Docs
@router.post("/token", tags=["Auth"])
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    user = await get_user_by_email(username)
    if not user or not checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=timedelta(minutes=300)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# TODO: Testing
@router.get("/users/me", tags=["Users"])
def get_me(current_user: dict = Depends(get_current_user)):
    print(current_user)
    return {"name": current_user["name"]}
