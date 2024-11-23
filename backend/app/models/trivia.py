from pydantic import BaseModel, conlist, conint, constr, validator
from app.core.constants import TRIVIA_STATUS
from typing import Optional, List

class Trivia(BaseModel):
    name: constr(min_length=1)
    description: str
    question_ids: conlist(str, min_length=1)
    user_ids: conlist(str, min_length=1)
    round_time_sec: Optional[conint(ge=1, le=3600)] = 60

class TriviaInDB(Trivia):
    id: str
    status: str
    joined_users: Optional[List[str]] = []

    # Validación para el campo `status`
    @validator("status")
    def validate_status(cls, value):
        allowed_statuses = TRIVIA_STATUS  # Definimos los estados permitidos
        if value not in allowed_statuses:
            raise ValueError(f"El estado debe ser uno de los siguientes: {allowed_statuses}")
        return value

# Usado para reiniciar una trivia de status "playing" a los campos iniciales de "waiting_start"
class TriviaClean(Trivia):
    status: str

    # Validación para el campo `status`
    @validator("status")
    def validate_status(cls, value):
        allowed_statuses = TRIVIA_STATUS  # Definimos los estados permitidos
        if value not in allowed_statuses:
            raise ValueError(f"El estado debe ser uno de los siguientes: {allowed_statuses}")
        return value
