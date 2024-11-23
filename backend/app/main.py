from fastapi import FastAPI
from app.works.trivia_runner import start_check_trivias_task, stop_check_trivias_task
from app.routes.user_routes import router as user_router
from app.routes.question_routes import router as question_routes
from app.routes.trivia_routes import router as trivia_routes

# FUTURE: Si todos los jugadores responden una ronda y aun hay tiempo, la ronda termina y pasa a la siguiente

app = FastAPI(
    title="My API",
    description="API para la gestión de usuarios y autenticación.",
    version="1.0.0",
)

# Registro de rutas
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
    return {"message": "Welcome to the API"}
