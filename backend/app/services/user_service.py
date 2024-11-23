from typing import Optional
from bcrypt import gensalt, hashpw
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.user import UserCreate, UserResponse, UserFull
from app.core.config import db

users_collection: AsyncIOMotorCollection = db["users"]
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def create_user(user: UserCreate) -> UserResponse:
    user_dict = user.dict()
    salt = gensalt()
    hashed_password = hashpw(user.password.encode("utf-8"), salt)
    user_dict["password"] = hashed_password.decode("utf-8")
    user_dict["role"] = user_dict.get("role", "player")
    result = await users_collection.insert_one(user_dict)
    return UserResponse(id=str(result.inserted_id), **user.dict(exclude={"password"}))

async def get_user_by_email(email: str) -> Optional[UserFull]:
    user = await users_collection.find_one({"email": email})
    if user:
        # TODO: No es necesario que retorne un modelo
        return UserFull(id=str(user["_id"]), **user)

async def get_all_users():
    users = await users_collection.find().to_list(100)
    return [UserResponse(id=str(user["_id"]), **user) for user in users]

"""
"""
async def get_trivias_invitations_for_user(user_email: str) -> list:
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])
    query = {"user_ids": user_id, "status": "waiting_start"}
    trivias = await trivia_collection.find(query).to_list(100)
    trivia_ids = [str(trivia["_id"]) for trivia in trivias]
    return trivia_ids


async def get_trivia_joined(user_email: str) -> dict:
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    # Buscar la trivia donde el usuario esté y cuyo estado no sea 'ended'
    trivia = await trivia_collection.find_one(
        {"joined_users": user_id, "status": {"$ne": "ended"}}
    )
    if trivia:
        return {
            "trivia_id": str(trivia["_id"]),
            "status": trivia["status"]
        }
    return None

async def get_trivias_played_by_user(user_email: str) -> list:
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])
    trivias = await trivia_collection.find({
        "user_ids": user_id,
        "status": "ended"
    }).to_list(length=None)
    return [str(trivia["_id"]) for trivia in trivias]
