from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError, InvalidURI

from config import DB_NAME, MONGO_SERVER_SELECTION_TIMEOUT_MS, MONGO_URL, logger

# Zeabur/Kubernetes can inject connection strings that Motor cannot parse
# (e.g. a "tcp://host:port" service address, a value missing the mongodb://
# scheme, or credentials with unescaped special characters). Constructing the
# client eagerly at import time means any such value crashes the process before
# Uvicorn can bind a port, producing a container BackOff/restart loop. Building
# it defensively keeps the API up so /health responds and /ready reports 503
# until the connection string is corrected.
_FALLBACK_MONGO_URL = "mongodb://localhost:27017"


def _build_client(mongo_url: str) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    )


def create_client(mongo_url: str) -> AsyncIOMotorClient:
    try:
        return _build_client(mongo_url)
    except (InvalidURI, ConfigurationError, ValueError) as exc:
        logger.error(
            "Invalid MongoDB connection string (%r); the API will start but "
            "database access will fail until MONGO_URL/MONGODB_URI is fixed. "
            "Error: %s",
            mongo_url,
            exc,
        )
        return _build_client(_FALLBACK_MONGO_URL)


client = create_client(MONGO_URL)
db = client[DB_NAME]


async def close_db_client():
    client.close()
