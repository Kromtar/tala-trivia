import time
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.trivia import Trivia, TriviaInDB
from datetime import datetime
from app.models.question import QuestionPlayer
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

"""
Permite a un Usuario unirse a una Trivia donde esta invitado (su id esta en los "user_ids" de la trivia).
La invitacion solo se concreta si la Trivia esta en status "waiting_start".
La invitacion solo se concreta si el usuario no esta en  "joined_users" de ninguna
otra Trivia que este en status "waiting_start" o "playing".
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

"""
Permite a un usuario retirarse de una Trivia donde se haya unido.
Esto solo es posible si la Trivia esta en status "waiting_start" y aun no ha partido.
En caso contrario el usuario no se puede retirar y debe esperar que la Trivia termine.
"""
async def leave_trivia(trivia_id: str, user_email: str) -> str:
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        raise HTTPException(status_code=404, detail="Trivia no encontrada")

    if user_id not in trivia["joined_users"]:
        raise HTTPException(status_code=400, detail="El usuario no está unido a esta trivia")

    if trivia["status"] != "waiting_start":
        raise HTTPException(status_code=400, detail="Solo puedes salir de trivias con estado 'waiting_start'")

    updated_trivia = await trivia_collection.find_one_and_update(
        {"_id": ObjectId(trivia_id)},
        {"$pull": {"joined_users": user_id}}
    )

    if not updated_trivia:
        raise HTTPException(status_code=404, detail="Error al intentar salir de la trivia")

    return str(updated_trivia["_id"])

# TODO: El modelo de retorno es dinamico
# TODO: Este endpoint debe retornar el historia de la Trivia sin pistas al usuario
# TODO: Usado para poder ver tanto donde puedo participar, la dinamica de una partida en curso
# y los resultados de una partida historica
async def get_trivia_details(trivia_id: str, user_email: str):
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        raise HTTPException(status_code=404, detail="Trivia no encontrada")

    if user_id not in trivia["user_ids"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta trivia")

    # TODO: Esto debe ser dinamico dependiendo si es admin o usuario y el estado del juego
    # if user["role"] == "admin":
    return TriviaInDB(id=str(trivia["_id"]), **trivia)

    # if trivia["status"] == "waiting_start":
    #     return TriviaInvitation(id=str(trivia["_id"]), **trivia)

async def get_question_for_trivia(trivia_id: str, user_email: str) -> QuestionPlayer:
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        raise HTTPException(status_code=404, detail="Trivia no encontrada")

    if user_id not in trivia["user_ids"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta Trivia")

    if trivia["status"] != "playing":
        raise HTTPException(status_code=400, detail="Esta Trivia no esta activa")

    # La pregunta que corresponde mostrar al usuario es aquella que aun no tiene aun el campo "round_score"
    active_question = next((q for q in trivia["rounds"] if "round_score" not in q), None)

    if not active_question:
        raise HTTPException(status_code=400, detail="No hay una pregunta activa en esta Trivia")

    # Verificar si el usuario ya respondió la pregunta
    answered_status = "not answered"
    for response in active_question.get("responses", []):
        if response["user_id"] == user_id:
            answered_status = "answered"
            break

    # Obtener el tiempo restante para la ronda
    current_time = int(time.time())
    round_endtime_timestamp = active_question["round_endtime"].timestamp()
    round_timeleft = round(max(0, round_endtime_timestamp - current_time))

    # Formatear la respuesta con los detalles de la pregunta activa
    return QuestionPlayer(
        id=active_question["id"],
        question=active_question["question"],
        possible_answers=active_question["possible_answers"],
        difficulty=active_question["difficulty"],
        round_count=active_question["round_count"],
        round_timeleft=round_timeleft,
        answered=answered_status
    )


async def submit_answer(trivia_id: str, question_id: str, answer_index: int, user_email: str):
    # Verificar que el usuario exista
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_id = str(user["_id"])

    # Verificar que la trivia exista
    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        raise HTTPException(status_code=404, detail="Trivia no encontrada")

    # Verificar que el usuario esté en la trivia
    if user_id not in trivia["user_ids"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta Trivia")

    # Verificar que la trivia esté en estado "playing"
    if trivia["status"] != "playing":
        raise HTTPException(status_code=400, detail="Esta Trivia no está activa")

    # Verificar que la pregunta exista y sea la activa
    question = next((q for q in trivia["rounds"] if q["id"] == question_id and "round_score" not in q), None)
    if not question:
        raise HTTPException(status_code=404, detail="La pregunta no existe o ya ha finalizado")

    # Verificar que la respuesta esté dentro del tiempo permitido
    current_time = datetime.utcnow()
    if current_time >= question["round_endtime"]:
        raise HTTPException(status_code=400, detail="El tiempo para responder esta pregunta ha expirado")

    # Validar si el usuario ya respondió esta pregunta
    existing_response = next((resp for resp in question.get("responses", []) if resp["user_id"] == user_id), None)
    if existing_response:
        raise HTTPException(status_code=400, detail="El usuario ya respondió esta pregunta,\
             no puedes cambiar tu respuesta")

    # Validar que answer_index esté dentro del rango permitido
    possible_answers = question.get("possible_answers", [])
    if not (0 < answer_index <= len(possible_answers)):
        raise HTTPException(
            status_code=400,
            detail=f"El índice de respuesta debe estar entre 1 y {len(possible_answers)}"
        )

    response_data = {
        "user_id": user_id,
        "answer_index": answer_index,
        "submitted_at": current_time
    }

    result = await trivia_collection.update_one(
        {"_id": ObjectId(trivia_id), "rounds.id": question_id},
        {"$push": {"rounds.$.responses": response_data}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No se pudo registrar la respuesta")

    return {
        "message": "Respuesta enviada correctamente"
    }