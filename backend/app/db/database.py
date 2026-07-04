from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


# Create MongoDB client
client = AsyncIOMotorClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=5000,
)


# Select database
database = client[settings.DATABASE_NAME]