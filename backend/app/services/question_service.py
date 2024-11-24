from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.question import Question, QuestionInDB, QuestionUpdate
from app.core.config import db
from bson import ObjectId
from fastapi import HTTPException
from app.services.trivia_service import get_trivia

questions_collection: AsyncIOMotorCollection = db["questions"]

async def create_question(question: Question) -> QuestionInDB:
    """
    Crea una nueva pregunta
    """
    question_dict = question.dict()
    result = await questions_collection.insert_one(question_dict)
    return QuestionInDB(id=str(result.inserted_id), **question.dict())

async def get_all_questions() -> List[QuestionInDB]:
    """
    Recupera todas las preguntas
    """
    questions_cursor = questions_collection.find()
    questions = []
    async for question in questions_cursor:
        questions.append(QuestionInDB(id=str(question["_id"]), **question))
    return questions

async def get_question(question_id: str) -> Optional[QuestionInDB]:
    """
    Recupera una pregunta
    """
    result = await questions_collection.find_one({"_id": ObjectId(question_id)})
    if result:
        return QuestionInDB(id=str(result["_id"]), **result)
    return None


async def delete_question(question_id: str) -> Optional[QuestionInDB]:
    """
    Elimina una pregunta
    Solo se pueden eliminar preguntas que no estén asociadas a ninguna Trivia
    """
    trivia_using_question = await get_trivia(question_id, False)
    if trivia_using_question is not False:
        raise HTTPException(
            status_code=400,
            detail=f"La pregunta con ID {question_id} no puede eliminarse porque está\
                asociada a la Trivia '{trivia_using_question['_id']}'."
        )
    result = await questions_collection.find_one_and_delete({"_id": question_id})
    if result:
        return QuestionInDB(id=str(result["_id"]), **result)
    return None

async def update_question(question_id: str, updated_question: QuestionUpdate) -> QuestionInDB:
    """
    Actualiza una pregunta
    La pregunta no puede estar asociada a ninguna Trivia para poder ser actualizada.
    """
    trivia_using_question = await get_trivia(question_id, False)
    if trivia_using_question is not False:
        raise HTTPException(
            status_code=400,
            detail=f"La pregunta con ID {question_id} no puede ser actualizada porque está\
                asociada a la Trivia '{trivia_using_question['_id']}'."
        )

    update_data = {k: v for k, v in updated_question.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No se han enviado campos para actualizar.")

    result = await questions_collection.find_one_and_update(
        {"_id": ObjectId(question_id)},
        {"$set": update_data},
        return_document=True
    )
    return result
