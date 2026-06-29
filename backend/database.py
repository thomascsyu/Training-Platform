from motor.motor_asyncio import AsyncIOMotorClient

from config import DB_NAME, MONGO_SERVER_SELECTION_TIMEOUT_MS, MONGO_URL

_client = None
_database = None


def get_db_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
        )
    return _client


def get_database():
    global _database
    if _database is None:
        _database = get_db_client()[DB_NAME]
    return _database


class LazyDatabase:
    def __getattr__(self, name):
        return getattr(get_database(), name)

    def __getitem__(self, name):
        return get_database()[name]


db = LazyDatabase()


async def close_db_client():
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None
