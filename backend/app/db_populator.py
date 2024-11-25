from fastapi import APIRouter
from app.core.config import db
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.user import UserCreate
from app.models.question import Question
from app.models.trivia import Trivia
from app.services.user_service import create_user
from app.services.trivia_service import create_trivia as create_trivia_service

router = APIRouter()

trivia_collection: AsyncIOMotorCollection = db["trivias"]
users_collection: AsyncIOMotorCollection = db["users"]
questions_collection: AsyncIOMotorCollection = db["questions"]

async def create_users():
    users = [
        {"name": "admin", "email": "admin@test.com", "password": "1234", "role": "admin"},
        {"name": "player1", "email": "player1@test.com", "password": "1234", "role": "player"},
        {"name": "player2", "email": "player2@test.com", "password": "1234", "role": "player"},
    ]
    users_ids = []
    for user in users:
        r = await create_user(
            UserCreate(
                name=user["name"],
                email=user["email"],
                password=user["password"],
                role=user["role"]
            ))
        users_ids.append(str(r.id))
    return users_ids

async def create_questions():
    questions = [
        {
            "question": "¿Cuál es el principal objetivo del proceso de selección de personal?",
            "distractors": [
                "Reducir los costos operativos de la empresa",
                "Capacitar a los empleados actuales",
                "Mejorar la cultura organizacional"
            ],
            "answer": "Encontrar al candidato que mejor se adapte a las necesidades del puesto",
            "difficulty": 2
        },
        {
            "question": "¿Qué documento legal establece las condiciones laborales de un empleado en una empresa?",
            "distractors": [
                "El informe de desempeño",
                "La carta de despido",
                "La política de recursos humanos"
            ],
            "answer": "El contrato de trabajo",
            "difficulty": 1
        },
        {
            "question": "¿Cuál de las siguientes es una técnica común utilizada en la evaluación del desempeño de los empleados?",
            "distractors": [
                "Entrevistas de salida",
                "Sesiones de capacitación",
                "Evaluación de clima organizacional"
            ],
            "answer": "Revisión de objetivos alcanzados",
            "difficulty": 3
        },
        {
            "question": "¿Qué significa el término 'rotación de personal'?",
            "distractors": [
                "La estrategia de promover empleados a cargos más altos",
                "El cambio de roles entre los empleados dentro de la empresa",
                "La cantidad de horas trabajadas por los empleados"
            ],
            "answer": "La cantidad de empleados que abandonan la empresa",
            "difficulty": 2
        },
    ]

    questions_ids = []
    for question in questions:
        new_question = Question(
            question=question["question"],
            distractors=question["distractors"],
            answer=question["answer"],
            difficulty=question["difficulty"]
        )
        r = await questions_collection.insert_one(new_question.dict())
        questions_ids.append(str(r.inserted_id))
    return questions_ids

async def create_trivia(users_ids, question_ids):
    await create_trivia_service(Trivia(
        name="Desafío en Recursos Humanos: ¿Cuánto sabes sobre la gestión de talento?",
        description="Pon a prueba tus conocimientos en el mundo de los Recursos Humanos con esta trivia. Desde el proceso de selección de personal hasta la gestión del desempeño y la rotación, cada pregunta te desafiará a demostrar tu comprensión sobre las prácticas y conceptos clave en la gestión del talento.",
        question_ids=question_ids,
        user_ids_invitations=users_ids[1:3],
        round_time_sec=60
    ))

@router.post("/db_populator", tags=["db_populator"])
async def db_populator():
    """
    Carga en la DB usuarios, preguntas y una trivia a modo de prueba
    """
    users_ids = await create_users()
    questions_ids = await create_questions()
    await create_trivia(users_ids, questions_ids)
    return
