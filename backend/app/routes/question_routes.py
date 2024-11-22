from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.models.question import Question, QuestionInDB, QuestionResponse
from app.services.question_service import create_question, get_all_questions, delete_question, get_next_question
from app.core.auth import admin_required

router = APIRouter()

# Crear una nueva pregunta
@router.post(
    "/questions/",
    response_model=QuestionInDB,
    status_code=201,  # TODO: Que hace esto ?
    summary="Crear una nueva pregunta",
    description="Este endpoint permite crear una nueva pregunta, \
        con sus posibles respuestas y dificultad.",
    tags=["Questions"]
)
async def create_question_endpoint(
    question: Question,
    current_role: dict = Depends(admin_required)
):
    return await create_question(question)

# Obtener todas las preguntas
@router.get(
    "/questions/",
    response_model=List[QuestionInDB],
    summary="Obtener todas las preguntas",
    description="Devuelve una lista con todas las preguntas registradas en el sistema. \
        Incluye las posibles respuestas, difucultad y solucion.",
    tags=["Questions"]
)
async def get_all_questions_endpoint(current_role: dict = Depends(admin_required)):
    return await get_all_questions()

# Eliminar una pregunta por ID
@router.delete(
    "/questions/{question_id}",
    response_model=QuestionInDB,
    summary="Elimina una pregunta",
    tags=["Questions"]
)
async def delete_question_endpoint(question_id: str, current_role: dict = Depends(admin_required)):
    deleted_question = await delete_question(question_id)
    if not deleted_question:
        raise HTTPException(status_code=404, detail="Question not found")
    return deleted_question

# TODO: Para testing
@router.get(
    "/questions/next",
    response_model=QuestionResponse,
    summary="Obtener la siguiente pregunta",
    description="Devuelve una pregunta de dificultad determinada\
         y sus respuestas posibles mezcladas.",
    tags=["Questions"],
)
async def next_question(
    difficulty: int = Query(..., ge=1, le=3),  # Aseguramos que la dificultad esté entre 1 y 3
    used_ids: Optional[List[str]] = Query([]),  # Ids de preguntas ya usadas
):
    question = await get_next_question(difficulty, used_ids)
    if not question:
        raise HTTPException(status_code=404, detail="No se encontró una preguntas")
    return question
