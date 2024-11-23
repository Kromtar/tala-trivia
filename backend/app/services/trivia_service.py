from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.trivia import Trivia, TriviaInDB
from app.core.config import db
from fastapi import HTTPException
from bson import ObjectId

trivia_collection: AsyncIOMotorCollection = db["trivias"]
users_collection: AsyncIOMotorCollection = db["users"]
questions_collection: AsyncIOMotorCollection = db["questions"]

"""
Crea una nueva Trivia compuesta de una serie de Questions y donde se invitan una serie de Usuarios
"""
# TODO: Invitar usando emails
async def create_trivia(trivia: Trivia) -> TriviaInDB:
    # Verificar si las IDs de los usuarios existen
    user_ids = [ObjectId(user_id) for user_id in trivia.user_ids]
    existing_users = await users_collection.find({"_id": {"$in": user_ids}}).to_list(len(user_ids))
    if len(existing_users) != len(user_ids):
        raise HTTPException(status_code=400, detail="Algunas IDs de usuario no existen en la base de datos")

    # Verificar si las IDs de las preguntas existen
    question_ids = [ObjectId(trivia_id) for trivia_id in trivia.question_ids]
    existing_questions = await questions_collection.find({"_id": {"$in": question_ids}}).to_list(len(question_ids))
    if len(existing_questions) != len(question_ids):
        raise HTTPException(status_code=400, detail="Algunas IDs de pregunta no existen en la base de datos")

    trivia_dict = trivia.dict()
    # Las Trivias inician en el status: "waiting_start"
    trivia_dict["status"] = "waiting_start"
    result = await trivia_collection.insert_one(trivia_dict)
    return TriviaInDB(id=str(result.inserted_id), **trivia_dict)

"""
Elimina una Trivia
"""
async def delete_trivia(trivia_id: str) -> Optional[TriviaInDB]:
    trivia = await trivia_collection.find_one_and_delete({"_id": ObjectId(trivia_id)})
    if trivia:
        return TriviaInDB(id=str(trivia["_id"]), **trivia)
    return None

"""
Retorna todas las Trivias cargadas en el sistema (independiente de su status)
"""
async def get_all_trivias() -> list:
    trivias = await trivia_collection.find().to_list(100)
    return [TriviaInDB(id=str(trivia["_id"]), **trivia) for trivia in trivias]

# Obtener las trivias de un usuario (se puede definir un status)
"""
Retorna las Trivias asociadas a un usuario.
Opcionalmente se puede especificar retornar solo trivias de un determinado status
"""
# TODO: Valdiar que el status sea uno de los 3 validos
async def get_trivias_by_user(user_id: str, status: Optional[str] = None) -> list:
    query = {"user_ids": user_id}
    if status:
        query["status"] = status
    trivias = await trivia_collection.find(query).to_list(100)
    return [TriviaInDB(id=str(trivia["_id"]), **trivia) for trivia in trivias]

"""
Permite a un Usuario unirse a una Trivia donde esta invitado (su id esta en los "user_ids" de la trivia).
La invitacion solo se concreta si la Trivia esta en status "waiting_start".
La invitacion solo se concreta si el usuario no esta en  "joined_users" de ninguna
otra Trivia qie este en status "waiting_start" o "playing".
O sea, solo se permite jugar, o querer jugar, a UNA Trivia simultaneamente.
El usuario es añadido a la lista de "joined_users" en caso de pasar las validaciones correspondientes.
"""
async def join_trivia(trivia_id: str, user_email: str) -> TriviaInDB:
    # Buscar el usuario por correo electrónico
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    # Verificar si el usuario ya está unido a otra trivia activa o por comenzar
    conflicting_trivia = await trivia_collection.find_one({
        "joined_users": user_id,
        "status": {"$in": ["waiting_start", "playing"]}
    })
    if conflicting_trivia:
        raise HTTPException(
            status_code=403,
            detail=f"El usuario ya está participando en otra trivia (ID: {str(conflicting_trivia['_id'])}) en\
                 estado '{conflicting_trivia['status']}'"
        )

    # Buscar la trivia por ID
    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        raise HTTPException(status_code=404, detail="Trivia no encontrada")

    # Verificar si el usuario es parte de `user_ids` (esta invitado)
    if user_id not in trivia["user_ids"]:
        raise HTTPException(
            status_code=403,
            detail="El usuario no esta invitado a esta Trivia"
        )

    # Verificar si el estado de la trivia permite la acción
    if trivia["status"] != "waiting_start":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede unir a esta trivia porque su estado actual es '{trivia['status']}'."
        )

    # Actualizar el campo `joined_users` añadiendo al usuario si no está ya en la lista
    joined_users = trivia.get("joined_users", [])
    if user_id not in joined_users:
        joined_users.append(user_id)
        await trivia_collection.update_one(
            {"_id": ObjectId(trivia_id)},
            {"$set": {"joined_users": joined_users}}
        )

    trivia["joined_users"] = joined_users
    return TriviaInDB(id=str(trivia["_id"]), **trivia)
