from fastapi import APIRouter, HTTPException, Depends, Path, Form
from typing import List, Union
from app.models.trivia import Trivia, TriviaInDB, TriviaProtected
from app.services.trivia_service import (
    create_trivia,
    delete_trivia,
    get_all_trivias,
    join_trivia,
    leave_trivia,
    get_trivia_details,
    get_question_for_trivia,
    submit_answer
)
from app.models.question import DisplayedQuestion
from app.core.auth import admin_required, player_or_admin_required

router = APIRouter()

@router.post(
    "/trivias/",
    response_model=TriviaInDB,
    status_code=201,
    summary="(Admin) Crear una nueva Trivia",
    description="Este endpoint permite crear una nueva trivia con nombre,\
         descripción, preguntas, usuarios y tiempo de ronda (en segundos).",
    tags=["Trivias"]
)
async def create_trivia_endpoint(
    trivia: Trivia,
    current_role: dict = Depends(admin_required)
):
    return await create_trivia(trivia)

@router.delete(
    "/trivias/{trivia_id}",
    response_model=TriviaInDB,
    summary="(Admin) Eliminar una Trivia",
    description="Este endpoint elimina una trivia por su ID.",
    tags=["Trivias"]
)
async def delete_trivia_endpoint(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia que se desea eliminar.",
    ),
    current_role: dict = Depends(admin_required)
):
    deleted_trivia = await delete_trivia(trivia_id)
    if not deleted_trivia:
        raise HTTPException(status_code=404, detail="Trivia not found")
    return deleted_trivia

@router.get(
    "/trivias/",
    response_model=List[TriviaInDB],
    summary="(Admin) Obtener todas las Trivias",
    description="Devuelve una lista con todas las Trivias registradas en el sistema.",
    tags=["Trivias"]
)
async def get_all_trivias_endpoint(current_role: dict = Depends(admin_required)):
    trivias = await get_all_trivias()
    return trivias

@router.post(
    "/trivias/{trivia_id}/join",
    response_model=TriviaProtected,
    summary="Unirse a una Trivia donde el usuario esta invitado",
    description="Permite a un usuario unirse a una Trivia si está listado en los invitados (user_ids). \
                Un usuario solo puede aceptar una invitación y jugar UNA Trivia en forma simultanea.",
    tags=["Trivias"]
)
async def join_trivia_endpoint(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia a la que el usuario quiere unirse.",
    ),
    current_user: dict = Depends(player_or_admin_required),
):
    return await join_trivia(trivia_id, current_user["email"])

@router.post(
    "/trivias/{trivia_id}/leave",
    response_model=str,
    response_description="ID de la Trivia de la que el usuario se ha retirado.",
    summary="Salir de una Trivia",
    description="Permite a un usuario salirse de una Trivia. Solo es posible si el juego aun no ha iniciado.\
        En caso contrario el usuario debe esperar que la Trivia actual termine.",
    tags=["Trivias"]
)
async def leave_trivia_endpoint(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia a la que el usuario quiere retirarse.",
    ),
    current_user: dict = Depends(player_or_admin_required),
):
    return await leave_trivia(trivia_id, current_user["email"])

@router.get(
    "/trivias/{trivia_id}",
    response_model=Union[TriviaInDB, TriviaProtected],
    summary="Obtener detalle de una Trivia",
    description="Permite al usuario ver el detalle de una Trivia. El usuario debe estar invitado, participando o\
        haber participado en la trivia para poder ver el detalle. Si el usuario no es administrador, se ocultaran\
        detalles para evitar trampas.",
    tags=["Trivias"]
)
async def get_trivia_details_endpoint(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia de la que se quiere saber el detalle.",
    ),
    current_user: dict = Depends(player_or_admin_required),
):
    return await get_trivia_details(trivia_id, current_user["email"])

@router.get(
    "/trivias/{trivia_id}/question",
    response_model=DisplayedQuestion,
    summary="Obtener la pregunta actual de una Trivia que este en juego.",
    description="El usuario puede obtener la pregunta y posibles respuestas de la ronda activa de una Trivia.\
        También retorna otra información como la dificultad de la ronda, el tiempo restante para responder\
        (en segundos), un aviso si el jugador ya ha respondido en esta ronda y otra metadata.",
    tags=["Trivias"]
)
async def get_question_for_trivia_endpoint(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia de la cual se quiere obtener la pregunta de la ronda activa",
    ),
    current_user: dict = Depends(player_or_admin_required),
):
    return await get_question_for_trivia(trivia_id, current_user["email"])


@router.post(
    "/trivias/{trivia_id}/questions/{question_id}/answer",
    response_model=str,
    response_description="Posición de la respuesta aceptada",
    summary="Enviar respuesta a una pregunta de Trivia",
    description="Permite al usuario enviar su respuesta para una pregunta activa en una Trivia.\
        El usuario debe enviar la posición de la respuesta correspondiente a las preguntas mostradas al\
        usar /trivias/{trivia_id}/question. La posición PARTE EN 1, por lo tanto si desea responder\
        usando la respuesta 2, debe indicar en answer_position 2.",
    tags=["Trivias"]
)
async def submit_answer_to_trivia_question(
    trivia_id: str = Path(
        ...,
        description="El identificador único de la Trivia en la cual el usuario esta jugando",
    ),
    question_id: str = Path(
        ...,
        description="El identificador único de la pregunta a la cual el usuario esta respondiendo.",
    ),
    answer_position: int = Form(
        ...,
        description="Posición de la respuesta que desea enviar a una determinada pregunta.\
            La posición PARTE EN 1.",
        example="2"
    ),
    current_user: dict = Depends(player_or_admin_required),
):
    return await submit_answer(trivia_id, question_id, answer_position, current_user["email"])