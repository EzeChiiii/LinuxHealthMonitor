# app/database.py
# Sets up the SQLAlchemy connection to Postgres and provides a
# reusable "get_db" function that FastAPI endpoints will use to
# get a database session per-request.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# The engine manages the actual connection pool to Postgres.
engine = create_engine(settings.database_url)

# Each request gets its own session from this factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that our SQLAlchemy models (in models.py) will inherit from.
Base = declarative_base()

# Dependency function FastAPI will call for every endpoint that needs
# database access. It opens a session, hands it to the endpoint, and
# guarantees it's closed afterward (even if the endpoint raises an error).
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()