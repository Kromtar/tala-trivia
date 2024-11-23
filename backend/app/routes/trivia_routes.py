from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.trivia import Trivia, TriviaInDB
from app.services.trivia_service import (
    create_trivia,
    delete_trivia,
    get_all_trivias,
    join_trivia,
    leave_trivia,
    get_trivia_details,
    get_question_for_trivia
)
from app.models.question import QuestionPlayer
from app.core.auth import admin_required, player_or_admin_required

router = APIRouter()

# Crear una nueva trivia
@router.post(
    "/trivias/",
    response_model=TriviaInDB,
    status_code=201,  # Esto indica el código HTTP que se devolverá cuando la creación sea exitosa
    summary="(Admin) Crear una nueva Trivia",
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
    summary="(Admin) Eliminar una Trivia",
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
    summary="(Admin) Obtener todas las Trivias",
    description="Devuelve una lista con todas las trivias registradas en el sistema.",
    tags=["Trivias"]
)
async def get_all_trivias_endpoint(current_role: dict = Depends(admin_required)):
    trivias = await get_all_trivias()
    return trivias

@router.post(
    "/trivias/{trivia_id}/join",
    response_model=TriviaInDB,
    summary="Unirse a una Trivia",
    description="Permite a un usuario unirse a una trivia si está listado en los `user_ids`. \
                 Si ya se unió antes, no lo añade de nuevo.",
    tags=["Trivias"]
)
async def join_trivia_endpoint(
    trivia_id: str,
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    return await join_trivia(trivia_id, current_user["email"])

@router.post(
    "/trivias/{trivia_id}/leave",
    response_model=str,
    summary="Salir de una Trivia",
    description="Permite a un usuario salirse de una Trivia. Solo es posible si el juego aun no ha emepzado.",
    tags=["Trivias"]
)
async def leave_trivia_endpoint(
    trivia_id: str,
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    return await leave_trivia(trivia_id, current_user["email"])


# TODO: Endpoint para ver todo el detalle de una trivia a la cual estoy siendo invitado, estoy jugando, historico
@router.get(
    "/trivias/{trivia_id}",
    summary="Obtener detalle de una Trivia",
    description="Permite al usuario ver el detalle de una Trivia. El usuario debe estar invitado, participando o\
        haber participado en la trivia para poder ver el detalle.",
    tags=["Trivias"]
)
async def get_trivia_details_endpoint(
    trivia_id: str,
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    return await get_trivia_details(trivia_id, current_user["email"])

@router.get(
    "/trivias/{trivia_id}/question",
    response_model=QuestionPlayer,
    summary="Obtener la pregunta actual de una Trivia",
    description="Permite al usuario ver la pregunta actual si la Trivia está esta en juego",
    tags=["Trivias"]
)
async def get_question_for_trivia_endpoint(
    trivia_id: str,
    current_user: dict = Depends(player_or_admin_required),  # Se obtiene el ID del usuario actual
):
    return await get_question_for_trivia(trivia_id, current_user["email"])


# TODO: Endpoint para enviar una respuesta a una trivia
