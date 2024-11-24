import os
from motor.motor_asyncio import AsyncIOMotorClient

"""
Ultra simple conexión con MongoDB usando Motor.

Dado el contexto del proyecto no se ha implementado un driver mas avanzado
(como mongoose).Solo se usan modelos de pydantic para la validación de campos,
no se han implementado schemas.
"""

MONGO_URI = str(os.getenv("MONGO_URI", ""))
client = AsyncIOMotorClient(MONGO_URI)

TEST_MODE = int(os.getenv("TEST_MODE", 0))
if TEST_MODE == 1:
    db = client["testdatabase"]
else:
    db = client["mydatabase"]
