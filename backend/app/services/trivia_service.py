import time
from typing import Optional, Union, List
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.trivia import Trivia, TriviaInDB, TriviaProtected
from datetime import datetime
from app.models.question import DisplayedQuestion
from app.models.user import UserRanking
from app.core.config import db
from app.services.user_service import get_user_by_email
from app.core.constants import QUESTION_STATUS
from fastapi import HTTPException
from bson import ObjectId

trivia_collection: AsyncIOMotorCollection = db["trivias"]
users_collection: AsyncIOMotorCollection = db["users"]
questions_collection: AsyncIOMotorCollection = db["questions"]

async def create_trivia(trivia: Trivia) -> TriviaInDB:
    """
    Crea una nueva Trivia compuesta de una serie de Questions y donde se invitan una serie de Usuarios
    Las Trivias creadas parten por defecto con status "waiting_start". Al crear una Trivia el sistema
    calcula la cantidad de rondas totales que tendrá (total_rounds), basándose en el numero de preguntas.
    """

    # Verificar si las IDs de los usuarios existen
    user_ids_invitations = [ObjectId(user_id) for user_id in trivia.user_ids_invitations]
    existing_users = await users_collection.find(
        {"_id": {"$in": user_ids_invitations}}).to_list(len(user_ids_invitations))
    if len(existing_users) != len(user_ids_invitations):
        raise HTTPException(status_code=400, detail="Algunas IDs de usuario no existen en la base de datos")

    # Verificar si las IDs de las preguntas existen
    question_ids = [ObjectId(trivia_id) for trivia_id in trivia.question_ids]
    existing_questions = await questions_collection.find({"_id": {"$in": question_ids}}).to_list(len(question_ids))
    if len(existing_questions) != len(question_ids):
        raise HTTPException(status_code=400, detail="Algunas IDs de pregunta no existen en la base de datos")

    trivia_dict = trivia.dict()
    trivia_dict["status"] = "waiting_start"
    trivia_dict["total_rounds"] = len(trivia_dict["question_ids"])
    result = await trivia_collection.insert_one(trivia_dict)
    return TriviaInDB(id=str(result.inserted_id), **trivia_dict)


async def delete_trivia(trivia_id: str) -> Optional[TriviaInDB]:
    """
    Elimina una Trivia
    """
    trivia = await trivia_collection.find_one_and_delete({"_id": ObjectId(trivia_id)})
    if trivia:
        return TriviaInDB(id=str(trivia["_id"]), **trivia)
    return None

async def get_all_trivias() -> List[TriviaInDB]:
    """
    Retorna todas las Trivias
    """
    trivias = await trivia_collection.find().to_list(100)
    return [TriviaInDB(id=str(trivia["_id"]), **trivia) for trivia in trivias]


async def get_trivia(trivia_id: str, http: bool = True) -> Union[bool, TriviaInDB]:
    """
    Retorna una Trivia

    Con "http=False" retornamos un False, en vez de una HTTPException, en caso de no encontrar una Trivia
    """

    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        if http is True:
            raise HTTPException(status_code=404, detail="Trivia no encontrada")
        return False
    return trivia

async def join_trivia(trivia_id: str, user_email: str) -> TriviaProtected:
    """
    Agrega a un usuario que este en al lista de invitados (user_ids_invitations) de una Trivia, a la
    lista de usuarios que han aceptado la invitación (joined_users).

    Agregar un usuario a "joined_users" solo es posible cuando el usuario NO esta:
    - En la "joined_users" de otra Trivia que este con status "playing" (en curso)
    - En la "joined_users" de otra Trivia que esta esperando que todos los jugadores
    confirmen la invitación (status "waiting_start")
    O sea, un usuario solo puede aceptar simultáneamente 1 invitación a una trivia que
    este por empezar o este en curso.
    """

    # Buscar el usuario por correo electrónico
    user = await get_user_by_email(user_email)
    user_id = user.id

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
    trivia = await get_trivia(trivia_id)

    # Verificar si el usuario es parte de `user_ids_invitations` (esta invitado)
    if user_id not in trivia["user_ids_invitations"]:
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
    return TriviaProtected(id=str(trivia["_id"]), **trivia)


async def leave_trivia(trivia_id: str, user_email: str) -> str:
    """
    Permite a un usuario retirarse de una Trivia donde se haya unido.

    Esto solo es posible si la Trivia esta en status "waiting_start" y aun no ha iniciado.
    En caso contrario, el usuario no se puede retirar y debe esperar que la Trivia donde participa termine.
    """

    # Buscar el usuario por correo electrónico
    user = await get_user_by_email(user_email)
    user_id = user.id

    # Buscar la trivia por ID
    trivia = await get_trivia(trivia_id)

    # Verificar si el usuario ha aceptado la invitación a la Trivia
    if user_id not in trivia["joined_users"]:
        raise HTTPException(status_code=400, detail="El usuario no está unido a esta trivia")

    # Verificar si el estado de la trivia permite la acción
    if trivia["status"] != "waiting_start":
        raise HTTPException(status_code=400, detail="Solo puedes salir de trivias con estado 'waiting_start'")

    # Remueve al usuario de la Trivia
    updated_trivia = await trivia_collection.find_one_and_update(
        {"_id": ObjectId(trivia_id)},
        {"$pull": {"joined_users": user_id}}
    )

    if not updated_trivia:
        raise HTTPException(status_code=404, detail="Error al intentar salir de la trivia")

    return str(updated_trivia["_id"])


async def get_trivia_details(trivia_id: str, user_email: str) -> Union[TriviaInDB, TriviaProtected]:
    """
    Retorna el detalle de una Trivia con la información de todas sus rondas (si es que existen).

    Si el usuario no es admin, la función se asegura de ocultar información sensible, durante la progresión
    de una ronda, para evitar trampas.
    """

    # Buscar el usuario por correo electrónico
    user = await get_user_by_email(user_email)
    user_id = user.id

    # Buscar la trivia por ID
    trivia = await get_trivia(trivia_id)

    # Si no es admin, verificar si el usuario es parte de la Trivia
    if user.role != 'admin' and user_id not in trivia["user_ids_invitations"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta trivia")

    # Verifica la cantidad de información a retornar dependiendo del rol del usuario
    if user.role == "player":
        for round_item in trivia.get("rounds", []):
            if "round_score" not in round_item:
                for response in round_item.get("responses", []):
                    if response["user_id"] != user_id:
                        response["answer_index"] = -1
        return TriviaProtected(id=str(trivia["_id"]), **trivia)

    return TriviaInDB(id=str(trivia["_id"]), **trivia)

async def get_question_for_trivia(trivia_id: str, user_email: str) -> DisplayedQuestion:
    """
    Retorna la Pregunta de la ronda activa de una Trivia que debe ser desplegada al usuario.

    El retorno incluye diversa meta-data de la partida de Trivia (numero ronda, tiempo restante...)
    El sistema identifica la pregunta "activa" de una Trivia, validando que ronda aun no
    tiene el campo "round_score" (el cual solo se crea una vez la ronda ha terminado y se han
    calculado los puntos respectivos)
    """

    # Buscar el usuario por correo electrónico
    user = await get_user_by_email(user_email)
    user_id = user.id

    # Buscar la trivia por ID
    trivia = await get_trivia(trivia_id)

    # Si no es admin, verificar si el usuario es parte de la Trivia
    if user.role != 'admin' and user_id not in trivia["user_ids_invitations"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta Trivia")

    # Verificar si el estado de la trivia permite la acción
    if trivia["status"] != "playing":
        raise HTTPException(status_code=400, detail="Esta Trivia no esta activa")

    # La pregunta que corresponde mostrar al usuario es aquella que aun no tiene aun el campo "round_score"
    active_question = next((q for q in trivia["rounds"] if "round_score" not in q), None)
    if not active_question:
        raise HTTPException(status_code=400, detail="No hay una pregunta activa en esta Trivia")

    # Antepone numero en el texto de la pregunta
    for pa_i in range(len(active_question["possible_answers"])):
        active_question["possible_answers"][pa_i] = f"{pa_i + 1}) {active_question['possible_answers'][pa_i]}"

    # Verificar si el usuario ya respondió la pregunta
    answered_status = QUESTION_STATUS[1]
    for response in active_question.get("responses", []):
        if response["user_id"] == user_id:
            answered_status = QUESTION_STATUS[0]
            break

    # Calculamos el tiempo restante de la ronda
    current_time = int(time.time())
    round_endtime_timestamp = active_question["round_endtime"].timestamp()
    remaining_time = round(max(0, round_endtime_timestamp - current_time))

    return DisplayedQuestion(
        remaining_time=remaining_time,
        answered=answered_status,
        total_rounds=trivia["total_rounds"],
        **active_question
    )

async def submit_answer(trivia_id: str, question_id: str, answer_index: int, user_email: str) -> str:
    """
    Registra la respuesta del usuario, ante una determinada pregunta de una ronda.

    La respuesta solo es aceptada si esta dentro del rango de tiempo valido de la ronda.
    El usuario no pueda cambiar su respuesta una vez registrada una.
    El sistema identifica la pregunta "activa" de una Trivia, validando que ronda aun no
    tiene el campo "round_score" (el cual solo se crea una vez la ronda ha terminado y se han
    calculado los puntos respectivos)
    """

    # Verificar que el usuario exista
    user = await get_user_by_email(user_email)
    user_id = user.id

    # Verificar que la trivia exista
    trivia = await get_trivia(trivia_id)

    # Verificar que el usuario esté en la trivia
    if user_id not in trivia["user_ids_invitations"]:
        raise HTTPException(status_code=403, detail="El usuario no está incluido en esta Trivia")

    # Verificar si el estado de la trivia permite la acción
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

    # Guarda respuesta
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

    return str(answer_index)


async def get_trivia_ranking(trivia_id: str) -> List[UserRanking]:
    """
    Retorna el Ranking de los jugadores de una Trivia
    """

    trivia = await get_trivia(trivia_id)
    if trivia is None:
        raise HTTPException(status_code=404, detail="Trivia no encontrada.")
    if trivia["status"] != "ended":
        raise HTTPException(status_code=400, detail="Esta Trivia no está finalizada")

    ranking = sorted(trivia["final_score"], key=lambda x: x['score'], reverse=True)
    players_details = []
    position = 1
    for score in ranking:
        user = await users_collection.find_one({"_id": ObjectId(score["user_id"])})
        players_details.append(UserRanking(position=position, name=user["name"], final_score=int(score["score"])))
        position += 1

    return players_details
