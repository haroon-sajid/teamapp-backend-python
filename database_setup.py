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
        # For SQLite databases, we need to check if team_id column exists
        if DATABASE_URL.startswith("sqlite"):
            # Use raw SQLite connection to check schema
            db_path = DATABASE_URL.replace("sqlite:///./", "")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Check if projects table has team_id column
                cursor.execute('PRAGMA table_info(projects)')
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'team_id' not in columns:
                    print("❌ team_id column missing from projects table")
                    print("🔧 Adding team_id column...")
                    
                    # Ensure teams table exists
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS teams (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR NOT NULL UNIQUE,
                            description VARCHAR,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Create default team if no teams exist
                    cursor.execute('SELECT COUNT(*) FROM teams')
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            'INSERT INTO teams (name, description) VALUES (?, ?)',
                            ('Default Team', 'Default team for existing projects')
                        )
                    
                    # Get default team ID
                    cursor.execute('SELECT id FROM teams LIMIT 1')
                    default_team_id = cursor.fetchone()[0]
                    
                    # Add team_id column with default value
                    cursor.execute(f'ALTER TABLE projects ADD COLUMN team_id INTEGER DEFAULT {default_team_id}')
                    
                    # Update existing projects
                    cursor.execute('UPDATE projects SET team_id = ? WHERE team_id IS NULL', (default_team_id,))
                    
                    conn.commit()
                    print("✅ Successfully added team_id column to projects table")
                
                else:
                    print("✅ Database schema is up to date")
                    
            finally:
                conn.close()
                
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
