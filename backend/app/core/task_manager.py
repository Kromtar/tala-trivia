import asyncio
from fastapi import HTTPException
from typing import Callable

class TaskManager:
    _instance = None  # Atributo para implementar el patrón singleton

    def __new__(cls, *args, **kwargs):
        """Implementación del patrón singleton."""
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialize()  # Inicialización de la instancia única
        return cls._instance

    def _initialize(self):
        """Inicializa el almacenamiento interno de tareas."""
        self._tasks = {}

    async def _worker(self, task_id: str, func: Callable, *args, **kwargs):
        """Ejecuta un trabajo arbitrario."""
        print(f"Worker {task_id} iniciado.", flush=True)
        try:
            await func(*args, **kwargs)
            print(f"Worker {task_id} completado.", flush=True)
        except asyncio.CancelledError:
            print(f"Worker {task_id} cancelado.", flush=True)
            raise
        except Exception as e:
            print(f"Worker {task_id} falló con error: {e}", flush=True)
            raise

    async def start_task(self, task_id: str, func: Callable, *args, **kwargs):
        """Inicia una nueva tarea con una función arbitraria."""
        if task_id in self._tasks:
            raise HTTPException(status_code=400, detail="La tarea ya está en ejecución")

        task = asyncio.create_task(self._worker(task_id, func, *args, **kwargs))
        self._tasks[task_id] = task
        return {"status": f"Tarea {task_id} iniciada"}

    async def get_task_status(self, task_id: str):
        """Consulta el estado de una tarea."""
        if task_id not in self._tasks:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        task = self._tasks[task_id]
        if task.done():
            if task.cancelled():
                status = "cancelada"
            elif task.exception():
                status = f"fallida: {task.exception()}"
            else:
                status = "completada"
        else:
            status = "en ejecución"

        return {"task_id": task_id, "status": status}

    async def stop_task(self, task_id: str):
        """Detiene una tarea."""
        if task_id not in self._tasks:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        task = self._tasks.pop(task_id)
        task.cancel()
        return {"status": f"Tarea {task_id} cancelada"}
