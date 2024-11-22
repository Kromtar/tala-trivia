from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.question import Question, QuestionInDB, QuestionResponse
from app.core.config import db
from random import shuffle

questions_collection: AsyncIOMotorCollection = db["questions"]

# Crea una nueva pretunta
async def create_question(question: Question) -> QuestionInDB:
    question_dict = question.dict()
    result = await questions_collection.insert_one(question_dict)
    return QuestionInDB(id=str(result.inserted_id), **question.dict())

# Obtener todas las preguntas
async def get_all_questions() -> List[QuestionInDB]:
    questions_cursor = questions_collection.find()
    questions = []
    async for question in questions_cursor:
        questions.append(QuestionInDB(id=str(question["_id"]), **question))
    return questions

# Eliminar una pregunta por ID
async def delete_question(question_id: str) -> Optional[QuestionInDB]:
    result = await questions_collection.find_one_and_delete({"_id": question_id})
    if result:
        return QuestionInDB(id=str(result["_id"]), **result)
    return None

# Endpoint que retorna una pregunta de dificultad determinada
# Se usa una lista de ids de preguntas ya usadas para evitar repeticiones
# Las posibles respuestas son entregadas mezcladas en conjunto a la correcta
# Se indica en el retorno el index de la respuesta correcta
async def get_next_question(difficulty: int, used_ids: Optional[List[str]] = None) -> Optional[QuestionInDB]:
    if used_ids is None:
        used_ids = []
    query = {"difficulty": difficulty}
    # Excluir preguntas ya usadas
    if used_ids:
        query["_id"] = {"$nin": [id for id in used_ids]}

    # Usar el operador $sample para seleccionar una pregunta aleatoria
    question = await questions_collection.aggregate([
        {"$match": query},  # Filtrar por dificultad y excluir preguntas usadas
        {"$sample": {"size": 1}}  # Obtener una pregunta aleatoria
    ]).to_list(length=1)

    if not question:
        return None
    question = question[0]

    # Crear la lista de posibles respuestas (distractores + respuesta correcta)
    possible_answers = question["distractors"] + [question["answer"]]
    shuffle(possible_answers)
    correct_answer_index = possible_answers.index(question["answer"])

    # Retornar la respuesta usando el modelo QuestionResponse
    return QuestionResponse(
        id=str(question["_id"]),
        question=question["question"],
        possible_answers=possible_answers,
        difficulty=question["difficulty"],
        correct_answer_index=correct_answer_index
    )
