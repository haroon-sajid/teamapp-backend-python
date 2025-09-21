"""
Database configuration for the Kanban Board application.
This file sets up SQLAlchemy with support for both SQLite (local) and PostgreSQL (production).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL configuration
# Use PostgreSQL for production (Render), SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanban_board.db")

# Handle PostgreSQL URL format for Render
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for local development
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(DATABASE_URL)

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
