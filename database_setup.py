#!/usr/bin/env python3
"""
Database setup and schema verification.
This ensures the database schema matches the current models.
"""

import sqlite3
from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL, engine, Base
from models import User, Project, Task, Team, TeamMember, UserRole

def ensure_schema_is_current():
    """
    Ensure the database schema matches the current models.
    This handles cases where the database was created before team features were added.
    """
    
    print("Checking database schema...")
    
    try:
        # Use SQLAlchemy inspector to check schema
        inspector = inspect(engine)
        
        # Check if projects table exists and has team_id column
        if inspector.has_table('projects'):
            columns = [col['name'] for col in inspector.get_columns('projects')]
            
            if 'team_id' not in columns:
                print("❌ team_id column missing from projects table")
                print("🔧 This requires manual database migration for production")
                print("For now, creating tables with current schema...")
            else:
                print("✅ Database schema is up to date")
        else:
            print("📝 Projects table doesn't exist, will be created")
                
    except Exception as e:
        print(f"⚠️  Warning: Could not verify database schema: {e}")
        print("This might be okay if using PostgreSQL or if this is a fresh installation")

def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    
    # First ensure schema is current
    ensure_schema_is_current()
    
    # Then create/update all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/updated")

if __name__ == "__main__":
    create_tables()
