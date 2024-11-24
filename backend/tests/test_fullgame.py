import httpx
import asyncio
import random
from app.main import app
from tests.test_light import test_general_1

async def test_player_login(client, email, password):
    """
    Valida el login de un usuario normal (player) y el retorno de token.
    Retorna el token de acceso.
    """
    login_data = {
        "username": email,
        "password": password
    }
    response = await client.post("/login", data=login_data)

    assert response.status_code == 200, f"Error al iniciar sesión: {response.text}"
    response_data = response.json()
    assert "access_token" in response_data, "No se retornó un token de acceso"
    return response_data["access_token"]

async def test_trivia_invitations(client, player_token, trivia_id):
    """
    Valida que el usuario pueda recuperar las IDs de las trivias donde está invitado.
    """

    response = await client.get(
        "/me/trivias_invitations",
        headers={"Authorization": f"Bearer {player_token}"}
    )

    assert response.status_code == 200, f"Error al obtener invitaciones: {response.text}"
    response_data = response.json()
    assert trivia_id in response_data, "Trivia ID no encontrado en la lista de invitaciones"
    return response_data

async def test_join_trivia(client, player_token, trivia_id, player_1_id):
    """
    Valida que el usuario Player pueda unirse a una Trivia donde está invitado.
    """

    response = await client.post(
        f"/trivias/{trivia_id}/join",
        headers={"Authorization": f"Bearer {player_token}"}
    )

    assert response.status_code == 200, f"Error al unirse a la Trivia: {response.text}"
    response_data = response.json()

    assert response_data["id"] == trivia_id, "El ID de la Trivia no coincide"
    assert player_1_id in response_data["joined_users"], "El jugador no esta en la lista de usuarios aceptados"
    return response_data


async def test_get_trivia_joined(client, player_token, expected_trivia_id, expected_status):
    """
    Valida que el usuario obtenga la ID de la Trivia en la que se ha unido.
    """

    response = await client.get(
        "/me/trivia_joined",
        headers={"Authorization": f"Bearer {player_token}"}
    )

    assert response.status_code == 200, f"Error al obtener la Trivia unida: {response.text}"
    response_data = response.json()

    assert response_data["trivia_id"] == expected_trivia_id, (
        f"La ID de la Trivia no coincide. Esperada: {expected_trivia_id}, Devuelta: {response_data['id']}"
    )
    assert response_data["status"] == expected_status, "El estado de la Trivia no es válido"
    return response_data

async def test_get_question_for_trivia(client, player_token, trivia_id, expected_round):
    """
    Valida que el jugador pueda obtener la pregunta actual de una Trivia en la que está jugando.
    """

    response = await client.get(
        f"/trivias/{trivia_id}/question",
        headers={"Authorization": f"Bearer {player_token}"}
    )

    assert response.status_code == 200, f"Error al obtener la pregunta de la Trivia: {response.text}"
    response_data = response.json()
    assert response_data["question"] is not None
    assert response_data["round_count"] == expected_round
    return response_data["id"]

async def test_get_round_correct_response(client, admin_token, trivia_id, round):
    """
    Usando un Admin, recuperamos la respuesta correcta de un Round
    """

    response = await client.get(
        f"/trivias/{trivia_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200, f"Error al obtener los detalles de la Trivia: {response.text}"
    response_data = response.json()
    return response_data["rounds"][round]["correct_answer_index"] + 1

async def test_get_finish_trivia(client, player_token, trivia_id):
    """
    Usando un Admin, recuperamos la respuesta correcta de un Round
    """

    response = await client.get(
        f"/trivias/{trivia_id}",
        headers={"Authorization": f"Bearer {player_token}"}
    )

    assert response.status_code == 200, f"Error al obtener los detalles de la Trivia: {response.text}"
    response_data = response.json()
    return response_data

async def test_submit_answer_to_trivia_question(client, player_token, trivia_id, question_id, answer_position):
    """
    Valida que el jugador pueda enviar una respuesta a una pregunta activa en una trivia.
    """

    response = await client.post(
        f"/trivias/{trivia_id}/questions/{question_id}/answer",
        headers={"Authorization": f"Bearer {player_token}"},
        data={"answer_position": answer_position}
    )

    assert response.status_code == 200, f"Error al enviar la respuesta: {response.text}"
    response_data = response.json()
    assert response_data == str(answer_position)

async def test_endgame(trivia_data, player_1_id, player_2_id):
    """
    Realiza una validación de la Trivia ya terminada
    """

    assert trivia_data['status'] == 'ended', f"Error: el status de la trivia\
         debería ser 'ended', pero es {trivia_data['status']}"

    # Validamos que el jugador 1 respondiera 2 veces
    player_1_responses = 0
    for round_data in trivia_data['rounds']:
        for response in round_data['responses']:
            if response['user_id'] == player_1_id:
                player_1_responses += 1
    assert player_1_responses == 2, f"Error: El jugador 1 debería haber respondido en 2 rondas,\
         pero ha respondido en {player_1_responses} rondas."

    # Validamos que el jugador 2 respondiera 1 vez
    player_2_responses = 0
    for round_data in trivia_data['rounds']:
        for response in round_data['responses']:
            if response['user_id'] == player_2_id:
                player_2_responses += 1
    assert player_2_responses == 1, f"Error: El jugador 2 debería haber respondido en 1 ronda\
        , pero ha respondido en {player_2_responses} rondas."

async def test_general_2():
    """
    Test que simula una partida completa de trivia
    """

    test_general_1_data = await test_general_1()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:

        # Login con Player 1
        player_1_email = test_general_1_data["users"][0].email
        player_1_password = test_general_1_data["users"][0].password
        player_1_id = test_general_1_data["users_ids"][0]
        player_1_token = await test_player_login(client, player_1_email, player_1_password)

        # Validamos lista de invitaciones
        await test_trivia_invitations(client, player_1_token, test_general_1_data["trivia_id"])

        # Aceptamos la invitación con Player 1
        await test_join_trivia(client, player_1_token, test_general_1_data["trivia_id"], player_1_id)

        # Validamos que la Trivia aun no ha iniciado, pero que el usuario esta inscrito
        await test_get_trivia_joined(client, player_1_token, test_general_1_data["trivia_id"], "waiting_start")

        # Login con Player 2
        player_2_email = test_general_1_data["users"][1].email
        player_2_password = test_general_1_data["users"][1].password
        player_2_id = test_general_1_data["users_ids"][1]
        player_2_token = await test_player_login(client, player_2_email, player_2_password)

        # Aceptamos la invitación con Player 2
        await test_join_trivia(client, player_2_token, test_general_1_data["trivia_id"], player_2_id)

        # Login con Player 3
        player_3_email = test_general_1_data["users"][2].email
        player_3_password = test_general_1_data["users"][2].password
        player_3_id = test_general_1_data["users_ids"][2]
        player_3_token = await test_player_login(client, player_3_email, player_3_password)

        # Aceptamos la invitación con Player 3
        await test_join_trivia(client, player_3_token, test_general_1_data["trivia_id"], player_3_id)

        # Validamos que la Trivia iniciara
        await asyncio.sleep(3)
        await test_get_trivia_joined(client, player_1_token, test_general_1_data["trivia_id"], "playing")

        # Recuperamos la primera pregunta
        question_id = await test_get_question_for_trivia(client, player_1_token, test_general_1_data["trivia_id"], 1)

        # Usamos el admin para recuperar la respuesta de la primera pregunta
        question_1_response = await test_get_round_correct_response(
            client,
            test_general_1_data["admin_access_token"],
            test_general_1_data["trivia_id"],
            0
        )

        # Enviamos con usuario 1 la respuesta correcta
        await test_submit_answer_to_trivia_question(
            client,
            player_1_token,
            test_general_1_data["trivia_id"],
            question_id,
            question_1_response
        )

        # Enviamos con usuario 2 una respuesta incorrecta
        numbers = [1, 2, 3, 4]
        numbers.remove(question_1_response)
        await test_submit_answer_to_trivia_question(
            client,
            player_2_token,
            test_general_1_data["trivia_id"],
            question_id,
            random.choice(numbers)
        )

        # Esperamos que termine la ronda
        print("Esperando fin de ronda 1")
        await asyncio.sleep(12)

        # Recuperamos la segunda pregunta
        question_id = await test_get_question_for_trivia(client, player_1_token, test_general_1_data["trivia_id"], 2)

        # Usamos el admin para recuperar la respuesta de la primera pregunta
        question_2_response = await test_get_round_correct_response(
            client,
            test_general_1_data["admin_access_token"],
            test_general_1_data["trivia_id"],
            1
        )

        # Enviamos con usuario 1 la respuesta correcta
        await test_submit_answer_to_trivia_question(
            client,
            player_1_token,
            test_general_1_data["trivia_id"],
            question_id,
            question_2_response
        )

        # Esperamos fin de juego
        print("Esperando fin de juego")
        await asyncio.sleep(12 * 3)

        finish_trivia = await test_get_finish_trivia(client, player_1_token, test_general_1_data["trivia_id"])

        await test_endgame(finish_trivia, player_1_id, player_2_id)

if __name__ == "__main__":
    asyncio.run(test_general_2())
