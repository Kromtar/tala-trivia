from typing import Optional
from bcrypt import gensalt, hashpw
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.user import UserCreate, UserResponse
from app.core.config import db

users_collection: AsyncIOMotorCollection = db["users"]

async def create_user(user: UserCreate) -> UserResponse:
    user_dict = user.dict()
    salt = gensalt()
    hashed_password = hashpw(user.password.encode("utf-8"), salt)
    user_dict["password"] = hashed_password.decode("utf-8")
    result = await users_collection.insert_one(user_dict)
    return UserResponse(id=str(result.inserted_id), **user.dict(exclude={"password"}))

async def get_user_by_email(email: str) -> Optional[UserResponse]:
    user = await users_collection.find_one({"email": email})
    if user:
        return UserResponse(id=str(user["_id"]), **user)

async def get_all_users():
    users = await users_collection.find().to_list(100)
    return [UserResponse(id=str(user["_id"]), **user) for user in users]
