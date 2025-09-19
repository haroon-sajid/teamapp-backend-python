"""
Database configuration for the Kanban Board application.
This file sets up SQLAlchemy with SQLite for data persistence.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL for SQLite
# The database file will be created in the same directory as this file
SQLALCHEMY_DATABASE_URL = "sqlite:///./kanban_board.db"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
Base = declarative_base()

# Dependency function to get database session
# This will be used in our route handlers
def get_db():
    """
    Create a new database session for each request.
    The session is closed after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
