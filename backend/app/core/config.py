from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://mongodb:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client["mydatabase"]
