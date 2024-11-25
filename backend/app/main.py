from fastapi import FastAPI
from app.works.trivia_runner import start_check_trivias_task, stop_check_trivias_task
from app.routes.user_routes import router as user_router
from app.routes.question_routes import router as question_routes
from app.routes.trivia_routes import router as trivia_routes
from app.db_populator import router as db_populator

# FUTURE: Si todos los jugadores responden una ronda y aun hay tiempo, la ronda termina y pasa a la siguiente
# FUTURE: Reemplazar el uso de IDs por emails para invitar jugadores a una Trivia

app = FastAPI(
    title="TalaTrivia API",
    description="API de TalaTrivia, el mejor juego del mundo mundial",
    version="0.4.2",
)

app.include_router(user_router)
app.include_router(question_routes)
app.include_router(trivia_routes)

# Ruta para facilitar prueba del proyecto
app.include_router(db_populator)

@app.on_event("startup")
async def startup_event():
    await start_check_trivias_task()

@app.on_event("shutdown")
async def shutdown_event():
    await stop_check_trivias_task()

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de TalaTrivia!"}
