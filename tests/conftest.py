"""Pytest configuration — set required env vars before backend imports."""
import os

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "learnhub_test")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only-32b")
