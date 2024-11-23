import asyncio
from datetime import datetime, timedelta
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from bson import ObjectId
from app.services.question_service import get_question_by_id
from app.services.trivia_service import get_trivia
from typing import Union

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
    trivia = await get_trivia(trivia_id)
    question_ids = set(trivia.get("question_ids", []))
    round_question_ids = set([question['id'] for question in trivia.get("rounds", [])])
    available_question_ids = list(question_ids - round_question_ids)
    if not available_question_ids:
        return False
    return available_question_ids[0]

# TODO: Aqui va la logica de una Trivia, o sea, el manejo de las rondas, preguntas, puntajes...
async def trivia_worker(trivia_id: str) -> None:
    print(f"Trabajando en la trivia {trivia_id}", flush=True)
    trivia = await get_trivia(trivia_id)

    round_count = 1
    while True:
        #Mientas existan preguntas sin usar
        question_id = await get_next_question_id(trivia_id)
        if question_id is False:
            break
        print(f"Pregunta seleccionada: {question_id}", flush=True)
        question = await get_question_by_id(question_id)
        if not question:
            print(f"No se encontró la pregunta con ID {question_id}", flush=True)
            continue
        
        #Calcula en que momento debe terminar la ronda
        current_time = datetime.utcnow()
        round_lapse = int(trivia["round_time_sec"])
        round_endtime = current_time + timedelta(seconds=round_lapse)

        #Añade la informacion de la ronda a la trivia
        round_data = question.dict()
        round_data["round_endtime"] = round_endtime
        round_data["round_count"] = round_count
        #TODO: Pasar el rounds a un modelo
        await trivia_collection.update_one(
            {"_id": ObjectId(trivia_id)},
            {
                "$push": {"rounds": round_data}
            }
        )

        #Esperamos que se cumpla el tiempo de la ronda
        print(f"Esperando fin de ronda en {round_lapse}", flush=True)
        await asyncio.sleep(round_lapse)

        #Recuperar las respuestas de cada jugador y compararlas con la real
        #Revelar respuesta correcta
        #Asignar puntaje de ronda a cada jugador (todos los que no responden obtienen 0 puntos)

        trivia = await get_trivia(trivia_id)

        # Obtener la lista de todos los jugadores de la trivia
        all_user_ids = set(trivia.get("user_ids", []))

        # Recorrer los rounds y procesar aquellos que no tengan la propiedad "round_score"
        for round_data in trivia.get("rounds", []):
            if "round_score" in round_data:
                continue  # Si ya tiene round_score, lo ignoramos

            # Inicializar el puntaje para este round
            round_score = []

            # Obtener el índice de la respuesta correcta y la dificultad
            correct_answer_index = round_data["correct_answer_index"]
            difficulty = round_data["difficulty"]

            # Calcular puntajes según las respuestas de los usuarios
            responded_user_ids = set()
            for response in round_data.get("responses", []):
                user_id = response["user_id"]
                responded_user_ids.add(user_id)
                answer_index = response["answer_index"]

                # Asignar puntaje si la respuesta es correcta
                score = difficulty if (answer_index - 1) == correct_answer_index else 0

                # Añadir el puntaje del usuario al round_score
                round_score.append({"user_id": user_id, "score": score})
           
            # Identificar usuarios que no respondieron
            non_responded_user_ids = all_user_ids - responded_user_ids
            for user_id in non_responded_user_ids:
                round_score.append({"user_id": user_id, "score": 0})

            # Obtener respuestas y la respuesta correcta
            correct_answer_index = round_data.get("correct_answer_index")
            possible_answers = round_data.get("possible_answers", [])
            if correct_answer_index is None or correct_answer_index >= len(possible_answers):
                raise ValueError(f"Índice de respuesta correcta inválido para el round {round_data['id']}")
            correct_answer_text = possible_answers[correct_answer_index]

            # Actualizar la base de datos con el puntaje calculado
            result = await trivia_collection.update_one(
                {"_id": ObjectId(trivia_id), "rounds.id": round_data["id"]},
                {"$set": {"rounds.$.round_score": round_score, "rounds.$.correct_answer": correct_answer_text}}
            )

            if result.modified_count == 0:
                raise ValueError(f"No se pudo actualizar el puntaje para el round {round_data['id']}")

            round_count += 1

    #Calcular el puntaje de final de cada jugador
    trivia = await get_trivia(trivia_id)
    # Crear un diccionario para almacenar los puntajes finales
    final_scores = {}

    # Recorrer los rounds y acumular los puntajes
    for round_data in trivia.get("rounds", []):
        for score_entry in round_data.get("round_score", []):
            user_id = score_entry["user_id"]
            score = score_entry["score"]

            if user_id in final_scores:
                final_scores[user_id] += score
            else:
                final_scores[user_id] = score
    
    # Formatear el resultado como una lista de diccionarios
    final_scores_list = [{"user_id": user_id, "score": score} for user_id, score in final_scores.items()]

    # Actualizar el documento en la base de datos
    # TODO: Pasar juego a finalizado
    await trivia_collection.update_one(
        {"_id": ObjectId(trivia_id)},
        {"$set": {"final_score": final_scores_list, "status": "ended"}}
        #{"$set": {"final_score": final_scores_list}}
    )

    #Pasar la partida a terminada
    print(f"Trivia {trivia_id} terminada.", flush=True)