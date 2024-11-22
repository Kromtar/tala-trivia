from pydantic import BaseModel, conlist, conint
from typing import List

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
