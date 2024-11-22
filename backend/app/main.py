from fastapi import FastAPI
from app.routes.user_routes import router as user_router

app = FastAPI(
    title="My API",
    description="API para la gestión de usuarios y autenticación.",
    version="1.0.0",
)

# Registro de rutas
app.include_router(user_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
