import asyncio
from fastapi import HTTPException
from typing import Callable

class TaskManager:
    """
    Clase Singleton para administrar task

    Con start_task es posible iniciar cualquier trabajo asíncrono definido como
    una función Callable. Cada work debe tener una ID única.
    """
    _instance = None

    def __new__(cls, *args, **kwargs) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._tasks = {}

    async def _worker(self, task_id: str, func: Callable, *args, **kwargs) -> None:
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

    async def start_task(self, task_id: str, func: Callable, *args, **kwargs) -> dict:
        if task_id in self._tasks:
            raise HTTPException(status_code=400, detail="La tarea ya está en ejecución")

        task = asyncio.create_task(self._worker(task_id, func, *args, **kwargs))
        self._tasks[task_id] = task
        return {"status": f"Tarea {task_id} iniciada"}

    async def get_task_status(self, task_id: str) -> dict:
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

    async def stop_task(self, task_id: str) -> dict:
        if task_id not in self._tasks:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        task = self._tasks.pop(task_id)
        task.cancel()
        return {"status": f"Tarea {task_id} cancelada"}
