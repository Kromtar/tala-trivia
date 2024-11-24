import asyncio
from datetime import datetime, timedelta
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from bson import ObjectId
from app.services.question_service import get_question
from app.services.trivia_service import get_trivia
from typing import Union
from random import shuffle

task_manager = TaskManager()
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def start_trivia(trivia_id: str) -> None:
    """
    Crea un job para gestionar la 'vida' de una nueva partida de trivia durante su estado de "playing"
    Cada trivia en estado "playing" esta gestionada por un job independiente que se encarga de 
    manejar los tiempos de cada ronda, las preguntas, respuestas, la asignación de puntos y el termino de la trivia.
    """
    try:
        result = await trivia_collection.update_one(
            {"_id": ObjectId(trivia_id)},
            {"$set": {"status": "playing"}}
        )
        if result.modified_count == 0:
            print(f"Error al iniciar la Trivia {trivia_id}", flush=True)
            return
        await task_manager.start_task(f"trivia_worker_{trivia_id}", trivia_worker, trivia_id)
        print(f"Trivia {trivia_id} iniciada correctamente", flush=True)
    except Exception as e:
        print(f"Error al iniciar la trivia {trivia_id}: {e}", flush=True)

async def get_next_question_id(trivia_id: str) -> Union[bool, str]:
    """
    Dada una trivia que en estado "playing", se retorna la ID de la siguiente pregunta (aun no desplegada)
    que debe ser mostrada a los jugadores.
    En caso que todas las preguntas ya fueron utilizadas, retorna False
    """
    trivia = await get_trivia(trivia_id, False)
    question_ids = set(trivia.get("question_ids", []))
    round_question_ids = set([question['id'] for question in trivia.get("rounds", [])])
    available_question_ids = list(question_ids - round_question_ids)
    if not available_question_ids:
        return False
    return available_question_ids[0]

async def set_next_question_in_trivia(trivia, round_count) -> Union[bool, int]:
    """
    Prepara y dispone una nueva pregunta para los jugadores de una Trivia

    Se calcula el tiempo limite para responder la pregunta
    Se combinan y barajan las posibles respuestas (distractores y correcta)
    Si no quedan mas preguntas para la Trivia, retornamos False
    """
    question_id = await get_next_question_id(trivia["_id"])
    if question_id is False:
        return False
    question = await get_question(question_id)

    # Calcula en que momento debe terminar esta ronda
    current_time = datetime.utcnow()
    round_lapse = int(trivia["round_time_sec"])
    round_endtime = current_time + timedelta(seconds=round_lapse)

    # Añade la pregunta seleccionada a la ronda de la Trivia
    round_data = question.dict()
    possible_answers = round_data["distractors"] + [round_data["answer"]]
    shuffle(possible_answers)
    round_data["possible_answers"] = possible_answers
    round_data["correct_answer_index"] = possible_answers.index(round_data["answer"])
    round_data["round_endtime"] = round_endtime
    round_data["round_count"] = round_count

    await trivia_collection.update_one(
        {"_id": ObjectId(trivia["_id"])},
        {"$push": {"rounds": round_data}}
    )

    return round_lapse

async def calculate_round_points(trivia_id) -> None:
    """
    Calcula los puntos de cada jugador al finalizar una ronda.

    Solo calcula los puntos de rondas que aun no estén calculadas.
    Asigna 0 puntos a jugadores que no respondieron.
    Deja disponible, en texto, la respuesta correcta de la ronda.
    """

    trivia = await get_trivia(trivia_id, False)
    all_user_ids = set(trivia.get("user_ids_invitations", []))
    for round_data in trivia.get("rounds", []):
        if "round_score" in round_data:
            continue
        round_score = []

        correct_answer_index = round_data["correct_answer_index"]
        difficulty = round_data["difficulty"]
        responded_user_ids = set()
        for response in round_data.get("responses", []):
            user_id = response["user_id"]
            responded_user_ids.add(user_id)
            answer_index = response["answer_index"]
            score = difficulty if (answer_index - 1) == correct_answer_index else 0
            round_score.append({"user_id": user_id, "score": score})

        # Identificar usuarios que no respondieron y asigna 0 puntos
        non_responded_user_ids = all_user_ids - responded_user_ids
        for user_id in non_responded_user_ids:
            round_score.append({"user_id": user_id, "score": 0})

        # Deja disponible la respuesta correcta (en texto) una vez calculados los puntos de la ronda
        correct_answer_index = round_data.get("correct_answer_index")
        possible_answers = round_data.get("possible_answers", [])
        if correct_answer_index is None or correct_answer_index >= len(possible_answers):
            raise ValueError(f"Índice de respuesta correcta inválido para el round {round_data['id']}")
        correct_answer_text = possible_answers[correct_answer_index]

        # Actualiza información de la ronda
        result = await trivia_collection.update_one(
            {"_id": ObjectId(trivia_id), "rounds.id": round_data["id"]},
            {"$set": {"rounds.$.round_score": round_score, "rounds.$.correct_answer": correct_answer_text}}
        )
        if result.modified_count == 0:
            raise ValueError(f"No se pudo actualizar el puntaje para el round {round_data['id']}")

async def calculate_final_points(trivia_id) -> None:
    """
    Calcula los puntos finales de cada jugador, dado los puntos de cada ronda.
    Pasa la Trivia al estado finalizado "ended"
    """

    trivia = await get_trivia(trivia_id, False)
    final_scores = {}
    for round_data in trivia.get("rounds", []):
        for score_entry in round_data.get("round_score", []):
            user_id = score_entry["user_id"]
            score = score_entry["score"]

            if user_id in final_scores:
                final_scores[user_id] += score
            else:
                final_scores[user_id] = score

    final_scores_list = [{"user_id": user_id, "score": score} for user_id, score in final_scores.items()]
    await trivia_collection.update_one(
        {"_id": ObjectId(trivia_id)},
        {"$set": {"final_score": final_scores_list, "status": "ended"}}
    )

async def trivia_worker(trivia_id: str) -> None:
    """
    Ciclo principal para gestionar las rondas de una Trivia
    Administra tiempos de cada ronda y los puntos asociados.
    """

    print(f"Trabajando en la trivia {trivia_id}", flush=True)

    trivia = await get_trivia(trivia_id, False)
    round_count = 1
    while True:
        # Procesa una nueva pregunta para los jugadores de la Trivia
        round_lapse = await set_next_question_in_trivia(trivia, round_count)
        if round_lapse is False:
            break
        # Esperamos el lapso de la ronda antes de cerrarla y pasar a la proxima
        await asyncio.sleep(round_lapse)
        # Calcula los puntos de cada jugador de la ronda recién finalizada
        await calculate_round_points(trivia_id)
        round_count += 1

    # Calcula puntos finales
    await calculate_final_points(trivia_id)

    print(f"Trivia {trivia_id} terminada.", flush=True)
