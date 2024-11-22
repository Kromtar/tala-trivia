from fastapi import FastAPI
from app.routes.user_routes import router as user_router
from app.routes.question_routes import router as question_routes
from app.routes.trivia_routes import router as trivia_routes

app = FastAPI(
    title="My API",
    description="API para la gestión de usuarios y autenticación.",
    version="1.0.0",
)

# Registro de rutas
app.include_router(user_router)
app.include_router(question_routes)
app.include_router(trivia_routes)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
