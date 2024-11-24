import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = str(os.getenv("MONGO_URI", ""))
client = AsyncIOMotorClient(MONGO_URI)

TEST_MODE = int(os.getenv("TEST_MODE", 0))
if TEST_MODE == 1:
    db = client["testdatabase"]
else:
    db = client["mydatabase"]