import httpx
import asyncio
from app.main import app
from app.core.config import db
from app.models.user import UserCreate
from app.models.question import Question
from app.models.trivia import Trivia

async def clean_db():
    """Vacía todas las colecciones antes de iniciar el test"""
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})

async def test_users_part_1(client):
    """
    Crea y valida usando el endpoint POST 4 usuarios, 3 jugadores 1 uno admin
    Retorna la información de los usuarios creados
    """
    users = [
        UserCreate(name="Player One", email="player1@example.com", password="password123", role="player"),
        UserCreate(name="Player Two", email="player2@example.com", password="password123", role="player"),
        UserCreate(name="Player Three", email="player3@example.com", password="password123", role="player"),
        UserCreate(name="Admin User", email="admin@example.com", password="adminpassword", role="admin")
    ]

    for user in users:
        response = await client.post("/users", json=user.model_dump())
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == user.email
        assert response_data["role"] == user.role

    return users

async def test_admin_login(client):
    """
    Valida el login de administrador y el retorno de token
    Retorna la token para uso de endpoints posteriores que requieran autorización
    """
    login_data = {
        "username": "admin@example.com",
        "password": "adminpassword"
    }
    response = await client.post("/login", data=login_data)

    assert response.status_code == 200
    response_data = response.json()
    return response_data["access_token"]

async def test_users_part_2(client, access_token, users):
    """
    Valida la creación de los usuarios mediante el endpoint GET
    Retorna las IDs de los usuarios de role player
    """
    response = await client.get("/users", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    created_users = response.json()
    created_user_ids = [user["id"] for user in created_users]
    assert len(created_user_ids) == len(users), "No se crearon todos los usuarios"

    users_ids = []
    for user in users:
        created_user = next(u for u in created_users if u["email"] == user.email)
        assert created_user["role"] == user.role, f"El role de {user.email} es incorrecto"
        assert created_user["name"] == user.name, f"El nombre de {user.email} es incorrecto"
        if created_user["role"] == "player":
            users_ids.append(created_user["id"])

    return users_ids

async def test_questions(client, access_token):
    """
    Crea y valida usando el endpoint POST y GET 4 preguntas
    Retorna las Ids de las preguntas
    """
    question_ids = []
    questions = [
        Question(
            question="¿Cuál es la capital de Francia?",
            distractors=["Madrid", "Berlin", "Rome"],
            answer="Paris",
            difficulty=2
        ),
        Question(
            question="¿En qué continente se encuentra Brasil?",
            distractors=["Asia", "Europa", "Antártida"],
            answer="América",
            difficulty=1
        ),
        Question(
            question="¿Qué elemento químico tiene el símbolo 'O'?",
            distractors=["Oro", "Osmio", "Oxígeno"],
            answer="Oxígeno",
            difficulty=1
        ),
        Question(
            question="¿Quién pintó la Mona Lisa?",
            distractors=["Van Gogh", "Pablo Picasso", "Claude Monet"],
            answer="Leonardo da Vinci",
            difficulty=3
        )
    ]

    for question in questions:
        response = await client.post(
            "/questions/",
            json=question.model_dump(),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["question"] == question.question
        assert response_data["answer"] == question.answer
        assert response_data["difficulty"] == question.difficulty
        question_ids.append(response_data["id"])

    response = await client.get("/questions/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    created_questions = response.json()
    assert len(created_questions) == len(questions), "No se crearon todas las preguntas"

    for question in questions:
        created_question = next(q for q in created_questions if q["question"] == question.question)
        assert created_question["question"] == question.question
        assert created_question["answer"] == question.answer
        assert created_question["difficulty"] == question.difficulty

    return question_ids

async def test_trivia_creation(client, access_token, questions, users):
    """
    Crea y valida la creación de una Trivia
    """

    trivia_data = Trivia(
        name="Trivia de Ejemplo",
        description="Trivia creada para prueba",
        question_ids=questions,
        user_ids=users,
        round_time_sec=10
    )

    response = await client.post(
        "/trivias/",
        json=trivia_data.model_dump(),
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 201, f"Error al crear la trivia: {response.text}"
    response_data = response.json()
    assert response_data["name"] == trivia_data.name
    assert response_data["description"] == trivia_data.description
    assert sorted(response_data["user_ids"]) == sorted(users)

    get_response = await client.get(
        f"/trivias/{response_data['id']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert get_response.status_code == 200, f"Error al obtener la trivia: {get_response.text}"
    get_response_data = get_response.json()

    assert get_response_data["name"] == trivia_data.name
    assert get_response_data["description"] == trivia_data.description
    assert sorted(get_response_data["user_ids"]) == sorted(users)
    assert sorted(get_response_data["question_ids"]) == sorted(questions)

    return get_response_data["id"]

async def test_general_1():
    """
    Test general que prueba la creación de usuarios, login, creación de preguntas y trivias
    """
    await clean_db()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        users = await test_users_part_1(client)
        access_token = await test_admin_login(client)
        users_ids = await test_users_part_2(client, access_token, users)
        question_ids = await test_questions(client, access_token)
        trivia_id = await test_trivia_creation(client, access_token, question_ids, users_ids)

        return {
            "users": users,
            "admin_access_token": access_token,
            "users_ids": users_ids,
            "question_ids": question_ids,
            "trivia_id": trivia_id
        }

if __name__ == "__main__":
    asyncio.run(test_general_1())
