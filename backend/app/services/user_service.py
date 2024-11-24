from typing import Union, List
from bcrypt import gensalt, hashpw
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.user import UserCreate, UserResponseInDB, UserFull
from app.core.config import db
from app.models.trivia import TriviaStatus

users_collection: AsyncIOMotorCollection = db["users"]
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def create_user(user: UserCreate) -> UserResponseInDB:
    """
    Crea un usuario

    El email debe ser único
    Dado el contexto del proyecto, la función permite crear usuarios con rol
    'player' y 'admin' sin restricciones.
    """
    existing_user = await get_user_by_email(user.email, False)
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya esta en uso")

    user_dict = user.dict()
    salt = gensalt()
    hashed_password = hashpw(user.password.encode("utf-8"), salt)
    user_dict["password"] = hashed_password.decode("utf-8")
    user_dict["role"] = user_dict.get("role", "player")
    result = await users_collection.insert_one(user_dict)
    return UserResponseInDB(id=str(result.inserted_id), **user.dict(exclude={"password"}))

async def get_user_by_email(email: str, http=True, full=False) -> Union[bool, UserFull, UserResponseInDB]:
    """
    Retorna un usuario

    Con "http=False" retornamos un False, en vez de una HTTPException, en caso de no encontrar el Usuario
    Con "full=True" retorna el hash de la password
    """

    user = await users_collection.find_one({"email": email})
    if not user:
        if http is True:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return False
    if full is True:
        return UserFull(id=str(user["_id"]), **user)
    return UserResponseInDB(id=str(user["_id"]), **user)

async def get_all_users() -> List[UserResponseInDB]:
    """
    Retorna todos los usuarios
    """

    users = await users_collection.find().to_list(100)
    return [UserResponseInDB(id=str(user["_id"]), **user) for user in users]

async def get_trivias_invitations_for_user(user_email: str) -> List[str]:
    """
    Retorna una lista de IDs de Trivias donde el usuario esta invitado

    Para distinguirlas de Trivias históricas y Trivias que estén en curso,
    se valida que el status de la Trivia sea "waiting_start".
    """

    user = await get_user_by_email(user_email, False)
    if user is False:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = user.id
    query = {"user_ids_invitations": user_id, "status": "waiting_start"}
    trivias = await trivia_collection.find(query).to_list(100)
    return [str(trivia["_id"]) for trivia in trivias]

async def get_trivia_joined(user_email: str) -> Union[bool, TriviaStatus]:
    """
    Retorna la ID de la Trivia donde el usuario ha aceptado una invitación.

    Ignora Trivias que ya han concluido y tienen un status "ended".
    """

    user = await get_user_by_email(user_email, False)
    if user is False:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = user.id

    trivia = await trivia_collection.find_one(
        {"joined_users": user_id, "status": {"$ne": "ended"}}
    )
    if trivia:
        return TriviaStatus(trivia_id=str(trivia["_id"]), status=trivia["status"])
    return False

async def get_trivias_played_by_user(user_email: str) -> List[str]:
    """
    Retorna una lista de IDs de Trivias donde el usuario haya participado
    """

    user = await get_user_by_email(user_email, False)
    if user is False:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = user.id
    trivias = await trivia_collection.find({
        "user_ids_invitations": user_id,
        "status": "ended"
    }).to_list(length=None)
    return [str(trivia["_id"]) for trivia in trivias]
