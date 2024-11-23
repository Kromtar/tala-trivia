from pydantic import BaseModel, conlist, conint
from typing import List, Optional
from datetime import datetime

class Question(BaseModel):
    question: str
    distractors: conlist(str, min_length=3, max_length=3)
    answer: str
    difficulty: conint(ge=1, le=3)

class QuestionInDB(Question):
    id: str

# Pregunta con posibles respuestas mezcladas, se indica el index de la correcta
class QuestionResponse(BaseModel):
    id: str
    question: str
    possible_answers: List[str]
    difficulty: int
    correct_answer_index: int

# Formato de pregunta entregada al usuario sin incluir informacion peligrosa
class QuestionPlayer(BaseModel):
    id: str
    question: str
    possible_answers: List[str]
    difficulty: int
    round_count: int
    round_timeleft: int
    answered: str
    total_rounds: int

class QuestionInTriviaResponses(BaseModel):
    user_id: str
    answer_index: int
    submitted_at: datetime

class QuestionInTriviaRoundScore(BaseModel):
    user_id: str
    score: int

# Formato de Question Guardado el coleccion Trivia
class QuestionInTrivia(BaseModel):
    id: str
    question: str
    possible_answers: List[str]
    difficulty: int
    correct_answer_index: int
    round_count: int
    round_endtime: datetime
    round_score: Optional[int] = 0
    responses: Optional[List[QuestionInTriviaResponses]] = []
    round_score: Optional[List[QuestionInTriviaRoundScore]] = []
