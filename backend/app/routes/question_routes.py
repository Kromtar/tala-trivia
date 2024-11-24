from fastapi import APIRouter, HTTPException, Depends, Path
from typing import List
from app.models.question import Question, QuestionInDB, QuestionUpdate
from app.services.question_service import (
    create_question,
    get_all_questions,
    delete_question,
    update_question
)
from app.core.auth import admin_required

router = APIRouter()

@router.post(
    "/questions/",
    response_model=QuestionInDB,
    status_code=201,
    summary="(Admin) Crear una nueva Pregunta",
    description="Este endpoint permite crear una nueva pregunta, \
        con sus posibles respuestas y dificultad [1 (Fácil), 2 (Intermedio), 3 (Difícil)].",
    tags=["Questions"]
)
async def create_question_endpoint(
    question: Question,
    current_role: dict = Depends(admin_required)
):
    return await create_question(question)

@router.get(
    "/questions/",
    response_model=List[QuestionInDB],
    summary="(Admin) Obtener todas las Preguntas",
    description="Devuelve una lista con todas las preguntas registradas en el sistema. \
        Incluye las posibles respuestas, dificultad y solución.",
    tags=["Questions"]
)
async def get_all_questions_endpoint(current_role: dict = Depends(admin_required)):
    return await get_all_questions()

@router.delete(
    "/questions/{question_id}",
    response_model=QuestionInDB,
    summary="(Admin) Elimina una Pregunta",
    description="Elimina una Pregunta. Solo se pueden eliminar preguntas que no\
        estén siendo usadas en ninguna Trivia.",
    tags=["Questions"]
)
async def delete_question_endpoint(
    question_id: str = Path(
        ...,
        description="El identificador único de la Pregunta que se desea eliminar.",
    ),
    current_role: dict = Depends(admin_required)
):
    deleted_question = await delete_question(question_id)
    if not deleted_question:
        raise HTTPException(status_code=404, detail="PRegunta no encontrada")
    return deleted_question

@router.put(
    "/questions/{question_id}",
    response_model=QuestionInDB,
    summary="(Admin) Editar una Pregunta",
    description="Edita una Pregunta. Solo se pueden editar preguntas que no estén asociadas\
        a ninguna Trivia.",
    tags=["Questions"]
)
async def update_question_endpoint(
    updated_question_data: QuestionUpdate,
    question_id: str = Path(
        ...,
        description="El identificador único de la Pregunta que se desea editar.",
    ),
    current_role: dict = Depends(admin_required)
):
    updated_question_data = await update_question(question_id, updated_question_data)
    if not updated_question_data:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada o no editable.")
    return updated_question_data
