from motor.motor_asyncio import AsyncIOMotorClient

from config import DB_NAME, MONGO_SERVER_SELECTION_TIMEOUT_MS, MONGO_URL

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
)
db = client[DB_NAME]


async def close_db_client():
    client.close()
