import asyncio
from datetime import datetime, timedelta
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from bson import ObjectId
from app.services.question_service import get_question_by_id

task_manager = TaskManager()
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def start_trivia(trivia_id: str):
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

#Obtiene la siguiente pregunta que no ha sido expuesta aun a los jugadores. Si no quedan mas, retorna False
async def get_next_question_id(trivia_id: str):
    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    question_ids = set(trivia.get("question_ids", []))
    round_question_ids = set([question['id'] for question in trivia.get("rounds", [])])
    available_question_ids = list(question_ids - round_question_ids)
    if not available_question_ids:
        print("Todas las preguntas ya han sido usadas.")
        return False
    return available_question_ids[0]

# TODO: Aqui va la logica de una Trivia, o sea, el manejo de las rondas, preguntas, puntajes...
async def trivia_worker(trivia_id: str):
    print(f"Trabajando en la trivia {trivia_id}", flush=True)
    trivia = await trivia_collection.find_one({"_id": ObjectId(trivia_id)})
    if not trivia:
        print("Trivia con id {trivia_id} no encontrada.")
        return False

    round_count = 0
    while True:
        round_count += 1

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

        await trivia_collection.update_many(
            {"_id": ObjectId(trivia_id)},  # Filtramos por la trivia que queremos actualizar
            {"$set": {"rounds.$[elem].round_score": 0}},  # Establece "round_score" a 0 en las rondas sin "round_score"
            array_filters=[{"elem.round_score": {"$exists": False}}]  # Solo modifica las rondas sin "round_score"
        )


    #Calcular el puntaje de final de cada jugador
    #Pasar la partida a terminada
    print(f"Trivia {trivia_id} terminada.", flush=True)