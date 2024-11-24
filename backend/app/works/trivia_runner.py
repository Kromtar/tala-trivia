import asyncio
from app.core.constants import TRIVIA_CHECK_SEC_INTERVAL
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from app.works.trivia_manager import start_trivia
from app.models.trivia import TriviaRollback
from bson import ObjectId

task_manager = TaskManager()
trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def check_trivias() -> None:
    """
    Verifica, de forma cíclica, si el juego de una trivia cumple las condiciones para iniciar.
    Las condiciones es que todos los jugadores invitados (user_ids_invitations) estén unidos a la trivia (joined_users).
    """
    is_running = True
    while is_running:
        try:
            trivias = await trivia_collection.find({"status": "waiting_start"}).to_list(length=None)
            for trivia in trivias:
                user_ids_invitations = set(trivia.get("user_ids_invitations", []))
                joined_users = set(trivia.get("joined_users", []))
                if user_ids_invitations == joined_users:
                    await start_trivia(trivia['_id'])
            await asyncio.sleep(TRIVIA_CHECK_SEC_INTERVAL)
        except asyncio.CancelledError:
            print("Tarea de revisión de trivias cancelada.", flush=True)
            break
        except Exception as e:
            print(f"Error en la tarea de revisión de trivias: {e}", flush=True)
            is_running = False

async def rollback_interrupted_trivias() -> None:
    """
    Retorna a un estado inicial/limpio de "waiting_start" cualquier trivia que fuera interrumpida por un
    reinicio del backend y que estuviera en estado "playing".
    """
    trivias_playing = await trivia_collection.find({"status": "playing"}).to_list(length=None)
    for trivia in trivias_playing:
        rollback_data = {key: trivia[key] for key in TriviaRollback.__fields__ if key in trivia}
        rollback_data["status"] = "waiting_start"
        rollback_trivia = TriviaRollback(**rollback_data)
        await trivia_collection.replace_one(
            {"_id": ObjectId(trivia["_id"])},
            rollback_trivia.dict()
        )

async def start_check_trivias_task() -> None:
    await rollback_interrupted_trivias()
    await task_manager.start_task("check_trivias_task", check_trivias)

async def stop_check_trivias_task() -> None:
    await task_manager.stop_task("check_trivias_task")
