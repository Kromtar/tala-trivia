import asyncio
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from app.works.trivia_manager import start_trivia
from app.models.trivia import TriviaClean
from bson import ObjectId

task_manager = TaskManager()
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def check_trivias():
    """Función periódica que revisa las trivias en 'waiting_start'."""
    is_running = True
    while is_running:
        try:
            trivias = await trivia_collection.find({"status": "waiting_start"}).to_list(length=None)
            for trivia in trivias:
                user_ids = set(trivia.get("user_ids", []))
                joined_users = set(trivia.get("joined_users", []))
                if user_ids == joined_users:
                    print(f"Esta partida debería iniciar: {trivia['_id']}", flush=True)
                    await start_trivia(trivia['_id'])
            await asyncio.sleep(3)  # Espera 3 segundos antes de la próxima iteración
        except asyncio.CancelledError:
            print("Tarea de revisión de trivias cancelada.", flush=True)
            break
        except Exception as e:
            print(f"Error en la tarea de revisión de trivias: {e}", flush=True)
            await asyncio.sleep(3)  # Reintentar después de un error

async def start_check_trivias_task():
    # Resetea cualquier trivia en status "playing" a su estado "waiting_start" y remueve a todos los "joined_users"
    trivias_playing = await trivia_collection.find({"status": "playing"}).to_list(length=None)
    for trivia in trivias_playing:
        clean_data = {key: trivia[key] for key in TriviaClean.__fields__ if key in trivia}
        clean_data["status"] = "waiting_start"
        clean_trivia = TriviaClean(**clean_data)
        await trivia_collection.replace_one(
            {"_id": ObjectId(trivia["_id"])},
            clean_trivia.dict()
        )

    await task_manager.start_task("check_trivias_task", check_trivias)

async def stop_check_trivias_task():
    await task_manager.stop_task("check_trivias_task")
