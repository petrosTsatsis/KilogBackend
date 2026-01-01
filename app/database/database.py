from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Create an engine to connect to PostgreSQL database
engine = create_engine(settings.DATABASE_URL, echo=True)

# SessionLocal class: Each instance represents a new DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the ORM models (used for table mapping)
Base = declarative_base()


# Dependency for using sessions in endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()