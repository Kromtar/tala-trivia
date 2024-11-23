import asyncio
from datetime import datetime
from app.core.task_manager import TaskManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.config import db
from bson import ObjectId

# Instancia de TaskManager
task_manager = TaskManager()

trivia_collection: AsyncIOMotorCollection = db["trivias"]

async def start_trivia(trivia_id: str):
    """Función que inicia una trivia, cambia su estado a 'playing' y ejecuta un worker con la trivia."""
    try:
        current_time = datetime.utcnow()  # Obtener el tiempo actual en UTC
        result = await trivia_collection.update_one(
            {"_id": ObjectId(trivia_id)},
            {"$set": {
                "status": "playing",
                "start_time": current_time
            }}
        )
        if result.modified_count == 0:
            print(f"Error al iniciar la Trivia {trivia_id}", flush=True)
            return

        await task_manager.start_task(f"trivia_worker_{trivia_id}", trivia_worker, trivia_id)
        print(f"Trivia {trivia_id} iniciada correctamente", flush=True)
    except Exception as e:
        print(f"Error al iniciar la trivia {trivia_id}: {e}", flush=True)

# TODO: Aqui va la logica de una Trivia, o sea, el manejo de las rondas, preguntas, puntajes...
async def trivia_worker(trivia_id: str):
    """Worker para ejecutar la trivia. Puedes colocar la lógica del juego aquí."""
    print(f"Trabajando en la trivia {trivia_id}", flush=True)
    # Simulación de trabajo que dura 10 segundos.
    await asyncio.sleep(10)
    print(f"Trivia {trivia_id} terminada.", flush=True)

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

# Configuración para iniciar la tarea
async def start_check_trivias_task():
    """Inicia la tarea que revisa las trivias periódicamente."""
    await task_manager.start_task("check_trivias_task", check_trivias)

async def stop_check_trivias_task():
    await task_manager.stop_task("check_trivias_task")
