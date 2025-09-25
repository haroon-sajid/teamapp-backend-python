#!/usr/bin/env python3
"""
Database migration script to add team_id column to projects table.
This handles the case where the database was created before team features were added.
"""

import os
from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL, engine, Base
from models import User, Project, Task, Team, TeamMember, UserRole

def migrate_database():
    """Migrate the database to add team_id column to projects table."""
    
    print(" Starting database migration...")
    
    try:
        # Create all tables first (this will create missing tables)
        Base.metadata.create_all(bind=engine)
        print(" All tables created/verified")
        
        # Check if projects table has team_id column
        inspector = inspect(engine)
        
        if inspector.has_table('projects'):
            columns = [col['name'] for col in inspector.get_columns('projects')]
            
            if 'team_id' not in columns:
                print(" Adding team_id column to projects table...")
                
                # Create a default team if none exists
                with engine.connect() as conn:
                    # Check if teams table has any data
                    result = conn.execute(text("SELECT COUNT(*) FROM teams"))
                    team_count = result.scalar()
                    
                    if team_count == 0:
                        print(" Creating default team...")
                        conn.execute(text("""
                            INSERT INTO teams (name, description, created_at) 
                            VALUES ('Default Team', 'Default team for existing projects', NOW())
                        """))
                        conn.commit()
                    
                    # Get the default team ID
                    result = conn.execute(text("SELECT id FROM teams LIMIT 1"))
                    default_team_id = result.scalar()
                    
                    # Add team_id column to projects table
                    if DATABASE_URL.startswith("postgresql"):
                        # PostgreSQL syntax
                        conn.execute(text(f"""
                            ALTER TABLE projects 
                            ADD COLUMN team_id INTEGER DEFAULT {default_team_id}
                        """))
                    else:
                        # SQLite syntax
                        conn.execute(text(f"""
                            ALTER TABLE projects 
                            ADD COLUMN team_id INTEGER DEFAULT {default_team_id}
                        """))
                    
                    # Update existing projects to have the default team_id
                    conn.execute(text(f"""
                        UPDATE projects 
                        SET team_id = {default_team_id} 
                        WHERE team_id IS NULL
                    """))
                    
                    conn.commit()
                    print(" Successfully added team_id column to projects table")
            else:
                print(" team_id column already exists in projects table")
        else:
            print(" Projects table doesn't exist, will be created with current schema")
            
        print(" Database migration completed successfully!")
        
    except Exception as e:
        print(f" Migration failed: {str(e)}")
        import traceback
        print(f" Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    migrate_database()
