from pydantic import BaseModel, conint, Field
from typing import List, Optional, Literal
from datetime import datetime
from app.core.constants import QUESTION_STATUS

class Question(BaseModel):
    question: str = Field(
        ...,
        description="El texto de la pregunta que será presentada al usuario.",
        example="¿Cuál es la capital de Francia?"
    )
    distractors: List[str] = Field(
        ...,
        description="Una lista de respuestas incorrectas que acompañarán a la respuesta correcta.",
        example=["Madrid", "Berlín", "Roma"]
    )
    answer: str = Field(
        ...,
        description="La respuesta correcta a la pregunta.",
        example="París"
    )
    difficulty: conint(ge=1, le=3) = Field(
        ...,
        description="El nivel de dificultad de la pregunta.\
            Valores permitidos: (1: Fácil, 2: Intermedio, 3: Difícil).",
        example=1
    )

class QuestionInDB(Question):
    id: str = Field(
        ...,
        description="El identificador único de la pregunta en la base de datos.",
        example="640f92a18b545c7b5f34f4b0"
    )


class QuestionUpdate(Question):
    question: Optional[str] = Field(
        None,
        description="El texto de la pregunta que será presentada al usuario.",
        example="¿Cuál es la capital de Alemania?"
    )
    distractors: Optional[List[str]] = Field(
        None,
        description="Una lista de respuestas incorrectas que acompañarán a la respuesta correcta.",
        example=["Ámsterdam", "Lisboa", "Copenhague"]
    )
    answer: Optional[str] = Field(
        None,
        description="La respuesta correcta a la pregunta.",
        example="Berlín"
    )
    difficulty: Optional[conint(ge=1, le=3)] = Field(
        None,
        description="El nivel de dificultad de la pregunta.\
            Valores permitidos: (1: Fácil, 2: Intermedio, 3: Difícil).",
        example=2
    )


"""
Modelo usado para entregar las preguntas al jugador durante una ronda
Esto implica los distractores y respuesta correcta mezclados, el tiempo
restante de la ronda, el contador de la ronda actual, la cantidad de
rondas totales y si esta ronda ya fue respondida por el jugador
"""

class DisplayedQuestion(BaseModel):
    id: str = Field(
        ...,
        description="El identificador único de la pregunta en la base de datos.",
        example="640f92a18b545c7b5f34f4b0"
    )
    question: str = Field(
        ...,
        description="El texto de la pregunta que será presentada.",
        example="¿Cuál es la capital de Francia?"
    )
    possible_answers: List[str] = Field(
        ...,
        description="Lista de respuestas posibles para la pregunta.",
        example=["Madrid", "Berlín", "Roma", "París"]
    )
    difficulty: conint(ge=1, le=3) = Field(
        ...,
        description="El nivel de dificultad de la pregunta (1: Fácil, 2: Intermedio, 3: Difícil).",
        example=1
    )
    round_count: int = Field(
        ...,
        description="El número de ronda en que se presenta la pregunta.",
        example=1
    )
    remaining_time: int = Field(
        ...,
        description="El tiempo restante en segundos para la ronda actual en segundos.",
        example=30
    )
    answered: Literal[tuple(QUESTION_STATUS)] = Field(
        ...,
        description="El estado de la pregunta para el usuario. Indica si ya ha respondido o no.\
            Posibles valores: ('answered', 'not answer'). Un jugador solo puede responder una vez\
            una pregunta y no puede cambiar su respuesta.",
        example="Aun no respondes esta pregunta"
    )
    total_rounds: int = Field(
        ...,
        description="El número total de rondas en la Trivia. Es igual al numero de preguntas que\
            estén asociadas a la Trivia.",
        example=5
    )


"""
Modelos usados para almacenar la dinámica de las Questions de dentro del modelo de Trivia.
Esto incluye las respuestas, puntos y tiempos asociados a todos los jugadores durante la ronda

El campo "correct_answer" solo adquiere valor cuando una ronda ha finalizado, es seguro dejarlo
en el modelo Protected.

El campo "correct_answer_index" debe ser ocultado de los jugadores y es utilizado para calcular
los puntos de los participantes.
"""

class QuestionInTriviaResponses(BaseModel):
    user_id: str = Field(
        ...,
        description="El identificador único del usuario que envió la respuesta.",
        example="640f92a18b545c7b5f34f4b0"
    )
    answer_index: int = Field(
        ...,
        description="El índice de la respuesta seleccionada por el usuario.\
        Este indice parte de 1, o sea, si responde con la segunda respuesta,\
        seria indice 2",
        example=2
    )
    submitted_at: datetime = Field(
        ...,
        description="La fecha y hora en que se envió la respuesta.",
        example="2024-11-24T15:30:00Z"
    )

class QuestionInTriviaRoundScore(BaseModel):
    user_id: str = Field(
        ...,
        description="El identificador único del usuario que recibió la puntuación en una ronda.",
        example="640f92a18b545c7b5f34f4b0"
    )
    score: int = Field(
        ...,
        description="La puntuación obtenida por el usuario en la ronda. Es 0 en caso de no responder.\
            La puntuación es igual a la dificultad de la pregunta respondida de forma correcta (1 a 3)",
        example=2
    )

class QuestionInTriviaProtected(BaseModel):
    id: str = Field(
        ...,
        description="El identificador único de la pregunta.",
        example="640f92a18b545c7b5f34f4b0"
    )
    question: str = Field(
        ...,
        description="El texto de la pregunta que será presentada.",
        example="¿Cuál es la capital de Francia?"
    )
    possible_answers: List[str] = Field(
        ...,
        description="Lista de respuestas posibles para la pregunta.",
        example=["Madrid", "Berlín", "Roma", "París"]
    )
    difficulty: conint(ge=1, le=3) = Field(
        ...,
        description="El nivel de dificultad de la pregunta (1: Fácil, 2: Intermedio, 3: Difícil).",
        example=1
    )
    round_count: int = Field(
        ...,
        description="El número de ronda en que se presenta la pregunta.",
        example=1
    )
    round_endtime: datetime = Field(
        ...,
        description="La fecha y hora en que finaliza la ronda para esa pregunta.\
            No se aceptan respuestas luego de este momento. Los usuarios que no\
            responden a tiempo reciben 0 puntos en la ronda.",
        example="2024-11-24T16:00:00Z"
    )
    correct_answer: Optional[str] = Field(
        default="",
        description="La respuesta correcta. Este campo solo se llena una vez que la ronda\
            ha finalizado. Tiene por objetivo que los jugadores puedan tener feedback\
            del juego.",
        example="París"
    )
    responses: Optional[List[QuestionInTriviaResponses]] = Field(
        default=[],
        description="Las respuestas enviadas por los usuarios durante la ronda."
    )
    round_score: Optional[List[QuestionInTriviaRoundScore]] = Field(
        default=[],
        description="La puntuación de cada usuario en la ronda. Se calcula al finalizar el tiempo\
            de la ronda."
    )

class QuestionInTriviaFull(QuestionInTriviaProtected):
    correct_answer_index: int = Field(
        ...,
        description="El índice de la respuesta correcta en la lista de respuestas posibles.\
            Este valor es para uso interno y nunca se presenta a los usuarios.",
        example=3
    )
