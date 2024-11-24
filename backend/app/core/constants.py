import os
# TODO: asegurar de usar en todas partes esto y validar
TRIVIA_STATUS = ["ended", "playing", "waiting_start"]
QUESTION_STATUS = ["answered", "not answer"]
ROLES = ["player", "admin"]
TRIVIA_CHECK_SEC_INTERVAL = 3
LOGIN_PATH = "/login"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("La variable de entorno SECRET_KEY no está definida o está vacía.")
