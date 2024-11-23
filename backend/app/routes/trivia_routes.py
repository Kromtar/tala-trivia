from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.models.trivia import Trivia, TriviaInDB
from app.services.trivia_service import create_trivia, delete_trivia, get_all_trivias, get_trivias_by_user, join_trivia
from app.core.auth import admin_required, player_or_admin_required

router = APIRouter()

# Crear una nueva trivia
@router.post(
    "/trivias/",
    response_model=TriviaInDB,
    status_code=201,  # Esto indica el código HTTP que se devolverá cuando la creación sea exitosa
    summary="Crear una nueva trivia",
    description="Este endpoint permite crear una nueva trivia con nombre,\
         descripción, preguntas, usuarios y tiempo de ronda.",
    tags=["Trivias"]
)
async def create_trivia_endpoint(
    trivia: Trivia,
    current_role: dict = Depends(admin_required)
):
    return await create_trivia(trivia)

# Eliminar una trivia por ID
@router.delete(
    "/trivias/{trivia_id}",
    response_model=TriviaInDB,
    summary="Eliminar una trivia",
    description="Este endpoint elimina una trivia por su ID.",
    tags=["Trivias"]
)
async def delete_trivia_endpoint(
    trivia_id: str,
    current_role: dict = Depends(admin_required)
):
    deleted_trivia = await delete_trivia(trivia_id)
    if not deleted_trivia:
        raise HTTPException(status_code=404, detail="Trivia not found")
    return deleted_trivia

# Endpoint para obtener todas las trivias
@router.get(
    "/trivias/",
    response_model=List[TriviaInDB],
    summary="Obtener todas las trivias",
    description="Devuelve una lista con todas las trivias registradas en el sistema.",
    tags=["Trivias"]
)
async def get_all_trivias_endpoint(current_role: dict = Depends(admin_required)):
    trivias = await get_all_trivias()
    return trivias


# Endpoint para obtener trivias por un usuario específico y estado
# TODO: Obtener la id desde el email que esta en la token
# TODO: Ruta "Mis trivias activas, "Mis Trivias historicas, "Mis trivias por jugar"
@router.get(
    "/trivias/user/{user_id}",
    response_model=List[TriviaInDB],
    summary="Obtener trivias por usuario y estado",
    description="Devuelve una lista con todas las trivias en las que el\
         usuario especificado esté listado. Se puede filtrar por estado.",
    tags=["Trivias"]
)
async def get_trivias_by_user_endpoint(
    user_id: str,
    status: Optional[str] = Query(
        None,
        enum=["ended", "playing", "waiting_start"],
        description="Filtrar por estado de la trivia"
    )
):
    trivias = await get_trivias_by_user(user_id, status)
    if not trivias:
        raise HTTPException(status_code=404, detail="No trivias found for this user")
    return trivias


@router.post(
    "/trivias/{trivia_id}/join",
    response_model=TriviaInDB,
    summary="Unirse a una trivia",
    description="Permite a un usuario unirse a una trivia si está listado en los `user_ids`. \
                 Si ya se unió antes, no lo añade de nuevo.",
    tags=["Trivias"]
)
async def join_trivia_endpoint(
    trivia_id: str,
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    return await join_trivia(trivia_id, current_user["email"])

# TODO: Endpoint para salirse de una trivia en caso que aun no empezara (sino debes esperar a que termine el juego)

# TODO: Endpoint para obtener listado de IDs trivias donde estoy invitado / estoy jugando / historico

# TODO: Endpoint para ver todo el detalle de una trivia a la cual estoy siendo invitado, estoy jugando, historico

# TODO: Endpoint para ver las pregutnas, dificultad y tiempo resptante de una trivia

# TODO: Endpoint para enviar una respuesta a una trivia
