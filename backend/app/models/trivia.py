from pydantic import BaseModel, conlist, conint, constr, Field
from app.core.constants import TRIVIA_STATUS
from typing import Optional, List, Literal
from app.models.question import QuestionInTriviaFull, QuestionInTriviaProtected

class Trivia(BaseModel):
    name: constr(min_length=1) = Field(
        ...,
        description="El nombre de la Trivia.",
        example="Geografía Mundial"
    )
    description: str = Field(
        ...,
        description="Una descripción breve de la Trivia, explicando su temática o reglas.",
        example="Trivia sobre capitales de países y geografía mundial."
    )
    question_ids: conlist(str, min_length=1) = Field(
        ...,
        description="Una lista de identificadores de las preguntas asociadas a esta Trivia.",
        example=["640f92a18b545c7b5f34f4b0", "640f92a18b545c7b5f34f4b1"]
    )
    user_ids_invitations: conlist(str, min_length=1) = Field(
        ...,
        description="Una lista de identificadores de los usuarios que están invitados a participar en la Trivia.",
        example=["640f92a18b545c7b5f34f4b0", "640f92a18b545c7b5f34f4b1", "640f92a18b545c7b5f34f4b0"]
    )
    round_time_sec: Optional[conint(ge=1, le=3600)] = Field(
        60,
        description="El tiempo asignado por ronda en segundos. El valor predeterminado es 60 segundos.",
        example=90
    )

class TriviaFinalScore(BaseModel):
    user_id: str = Field(
        ...,
        description="El identificador único del uno de los usuarios que ha completado la Trivia.",
        example="640f92a18b545c7b5f34f4b1"
    )
    score: int = Field(
        ...,
        description="La puntuación final del usuario en la Trivia.",
        example=85
    )

class TriviaInDB(Trivia):
    id: str = Field(
        ...,
        description="El identificador único de la Trivia en la base de datos.",
        example="640f92a18b545c7b5f34f4b0"
    )
    status: Literal[tuple(TRIVIA_STATUS)] = Field(
        ...,
        description="El estado actual de la Trivia. Puede ser 'ended', 'playing' o 'waiting_start'.",
        example="waiting_start"
    )
    total_rounds: int = Field(
        ...,
        description="El número total de rondas en la Trivia. Es igual al total de\
            Preguntas que conformen la Trivia",
        example=5
    )
    joined_users: Optional[List[str]] = Field(
        [],
        description="Una lista de identificadores de los usuarios que se han\
            aceptado participar en la Trivia. La Trivia parte de forma automática\
            cuando todos los usuarios invitados a la Trivia acepten participar",
        example=["640f92a18b545c7b5f34f4b0", "640f92a18b545c7b5f34f4b1"]
    )
    rounds: Optional[List[QuestionInTriviaFull]] = Field(
        [],
        description="Una lista de rondas, cada una contiene toda la información para administrar\
            la dinámica de una ronda. Esto incluye: La pregunta, posibles respuestas, el index\
            de la respuesta correcta, la dificultad de la ronda, el tiempo de termino de la ronda\
                la respuesta de cada usuario a las preguntas, sus puntos y otra metadata.",
        example=[
            {
                "id": "640f92a18b545c7b5f34f4b0",
                "question": "¿Cuál es la capital de Francia?",
                "possible_answers": ["Madrid", "Berlín", "Roma", "París"],
                "difficulty": 1,
                "round_count": 1,
                "round_endtime": "2024-11-24T16:00:00Z",
                "correct_answer": "París",
                "responses": [
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "answer_index": 3,
                        "submitted_at": "2024-11-24T15:30:00Z"
                    },
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "answer_index": 1,
                        "submitted_at": "2024-11-24T15:32:00Z"
                    }
                ],
                "round_score": [
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "score": 10
                    },
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "score": 0
                    }
                ],
                "correct_answer_index": 3
            }
        ]
    )
    final_score: Optional[List[TriviaFinalScore]] = Field(
        [],
        description="Una lista de las puntuaciones finales de cada usuario que participó en la trivia.",
        example=[{
            "user_id": "640f92a18b545c7b5f34f4b0",
            "score": 85
        }]
    )


"""
Modelo usado para hacer rollback de una Trivia que ha sido interrumpida durante
su status "playing".
"""

class TriviaRollback(Trivia):
    status: Literal[tuple(TRIVIA_STATUS)]
    total_rounds: int


"""
Modelo usado para mostrar al jugador el estado de una Trivia sin revelar información sensible.
"""

class TriviaProtected(BaseModel):
    id: str = Field(
        ...,
        description="El identificador único de la Trivia en la base de datos.",
        example="640f92a18b545c7b5f34f4b0"
    )
    name: constr(min_length=1) = Field(
        ...,
        description="El nombre de la Trivia.",
        example="Geografía Mundial"
    )
    description: str = Field(
        ...,
        description="Una descripción breve de la Trivia, explicando su temática o reglas.",
        example="Trivia sobre capitales de países y geografía mundial."
    )
    user_ids_invitations: conlist(str, min_length=1) = Field(
        ...,
        description="Una lista de identificadores de los usuarios que están invitados a participar en la Trivia.",
        example=["640f92a18b545c7b5f34f4b0", "640f92a18b545c7b5f34f4b1", "640f92a18b545c7b5f34f4b0"]
    )
    round_time_sec: Optional[conint(ge=1, le=3600)] = Field(
        60,
        description="El tiempo asignado por ronda en segundos. El valor predeterminado es 60 segundos.",
        example=90
    )
    status: Literal[tuple(TRIVIA_STATUS)] = Field(
        ...,
        description="El estado actual de la Trivia. Puede ser 'ended', 'playing' o 'waiting_start'.",
        example="waiting_start"
    )
    total_rounds: int = Field(
        ...,
        description="El número total de rondas en la Trivia. Es igual al total de\
            Preguntas que conformen la Trivia",
        example=5
    )
    joined_users: Optional[List[str]] = Field(
        [],
        description="Una lista de identificadores de los usuarios que se han\
            aceptado participar en la Trivia. La Trivia parte de forma automática\
            cuando todos los usuarios invitados a la Trivia acepten participar",
        example=["640f92a18b545c7b5f34f4b0", "640f92a18b545c7b5f34f4b1"]
    )
    rounds: Optional[List[QuestionInTriviaProtected]] = Field(
        [],
        description="Una lista de rondas, cada una contiene toda la información para administrar\
            la dinámica de una ronda. Se oculta información sensible para evitar trampas. Las\
            respuestas de los otros jugadores (answer_index) solo es añadida una vez que la ronda\
            ha terminado. Lo mismo para el valor (correct_answer).",
        example=[
            {
                "id": "640f92a18b545c7b5f34f4b0",
                "question": "¿Cuál es la capital de Francia?",
                "possible_answers": ["Madrid", "Berlín", "Roma", "París"],
                "difficulty": 1,
                "round_count": 1,
                "round_endtime": "2024-11-24T16:00:00Z",
                "correct_answer": "París",
                "responses": [
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "answer_index": 3,
                        "submitted_at": "2024-11-24T15:30:00Z"
                    },
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "answer_index": 1,
                        "submitted_at": "2024-11-24T15:32:00Z"
                    }
                ],
                "round_score": [
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "score": 10
                    },
                    {
                        "user_id": "640f92a18b545c7b5f34f4b1",
                        "score": 0
                    }
                ],
                "correct_answer_index": 3
            }
        ]
    )
    final_score: Optional[List[TriviaFinalScore]] = Field(
        [],
        description="Una lista de las puntuaciones finales de cada usuario que participó en la trivia.",
        example=[{
            "user_id": "640f92a18b545c7b5f34f4b0",
            "score": 85
        }]
    )

class TriviaStatus(BaseModel):
    trivia_id: str = Field(
        ...,
        description="El identificador único de la Trivia en la base de datos.",
        example="640f92a18b545c7b5f34f4b0"
    )
    status: Literal[tuple(TRIVIA_STATUS)] = Field(
        ...,
        description="El estado actual de la Trivia. Puede ser 'ended', 'playing' o 'waiting_start'.",
        example="waiting_start"
    )
