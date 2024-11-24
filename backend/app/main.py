from fastapi import FastAPI
from app.works.trivia_runner import start_check_trivias_task, stop_check_trivias_task
from app.routes.user_routes import router as user_router
from app.routes.question_routes import router as question_routes
from app.routes.trivia_routes import router as trivia_routes

# FUTURE: Si todos los jugadores responden una ronda y aun hay tiempo, la ronda termina y pasa a la siguiente
# TODO: Editar user_ids por algo mas similar a "invitaciones"

app = FastAPI(
    title="TalaTrivia API",
    description="API de TalaTrivia, el mejor juego del mundo mundial",
    version="0.4.2",
)

app.include_router(user_router)
app.include_router(question_routes)
app.include_router(trivia_routes)

@app.on_event("startup")
async def startup_event():
    await start_check_trivias_task()

@app.on_event("shutdown")
async def shutdown_event():
    await stop_check_trivias_task()

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de TalaTrivia!"}
