#!/usr/bin/env python3
"""
Migration script to add team_id column to the projects table.
This script handles existing projects by creating a default team if needed.
"""

import os
import sys
from sqlalchemy import create_engine, text, Column, Integer, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from database import DATABASE_URL, Base

def migrate_projects_add_team_id():
    """
    Add team_id column to projects table and handle existing data.
    Creates a default team for existing projects if needed.
    """
    try:
        # Handle PostgreSQL URL format for Render
        database_url = DATABASE_URL
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Create engine
        if database_url.startswith("sqlite"):
            engine = create_engine(database_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(database_url)
        
        print(f"Connecting to database: {database_url}")
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check if team_id column already exists
                if database_url.startswith("sqlite"):
                    # For SQLite, check table schema
                    result = conn.execute(text("PRAGMA table_info(projects)"))
                    columns = [row[1] for row in result.fetchall()]
                    if 'team_id' in columns:
                        print(" team_id column already exists in projects table")
                        trans.rollback()
                        return True
                else:
                    # For PostgreSQL, check information_schema
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'projects' AND column_name = 'team_id'
                    """))
                    if result.fetchone():
                        print(" team_id column already exists in projects table")
                        trans.rollback()
                        return True
                
                # Check if projects table exists
                if database_url.startswith("sqlite"):
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"))
                else:
                    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename='projects'"))
                
                if not result.fetchone():
                    print("  Projects table doesn't exist yet. Migration not needed.")
                    trans.rollback()
                    return True
                
                # Check if teams table exists
                if database_url.startswith("sqlite"):
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'"))
                else:
                    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename='teams'"))
                
                teams_table_exists = result.fetchone() is not None
                
                if not teams_table_exists:
                    print(" Teams table doesn't exist. Please run create_teams_table.py first.")
                    trans.rollback()
                    return False
                
                # Check if there are existing projects
                result = conn.execute(text("SELECT COUNT(*) FROM projects"))
                project_count = result.fetchone()[0]
                
                print(f"Found {project_count} existing projects")
                
                # If there are existing projects, we need to handle the migration
                if project_count > 0:
                    # Check if there's at least one team
                    result = conn.execute(text("SELECT COUNT(*) FROM teams"))
                    team_count = result.fetchone()[0]
                    
                    if team_count == 0:
                        # Create a default team for existing projects
                        print("Creating default team for existing projects...")
                        if database_url.startswith("sqlite"):
                            conn.execute(text("""
                                INSERT INTO teams (name, description, created_at) 
                                VALUES ('Default Team', 'Default team for migrated projects', CURRENT_TIMESTAMP)
                            """))
                            result = conn.execute(text("SELECT last_insert_rowid()"))
                        else:
                            result = conn.execute(text("""
                                INSERT INTO teams (name, description, created_at) 
                                VALUES ('Default Team', 'Default team for migrated projects', NOW()) 
                                RETURNING id
                            """))
                        
                        default_team_id = result.fetchone()[0]
                        print(f" Created default team with ID: {default_team_id}")
                    else:
                        # Use the first existing team as default
                        result = conn.execute(text("SELECT id FROM teams ORDER BY id LIMIT 1"))
                        default_team_id = result.fetchone()[0]
                        print(f"Using existing team with ID: {default_team_id} as default")
                else:
                    # No existing projects, we can safely add the column as NOT NULL
                    default_team_id = None
                
                # Add the team_id column
                print("Adding team_id column to projects table...")
                
                if database_url.startswith("sqlite"):
                    # SQLite approach: Add column as nullable first, then update values, then make it NOT NULL
                    if project_count > 0:
                        # Step 1: Add nullable column
                        conn.execute(text("ALTER TABLE projects ADD COLUMN team_id INTEGER"))
                        
                        # Step 2: Update existing projects with default team
                        conn.execute(text(f"UPDATE projects SET team_id = {default_team_id}"))
                        
                        # Step 3: For SQLite, we can't easily change column to NOT NULL, so we'll leave it as is
                        # but add a foreign key constraint if possible
                        print("  Note: SQLite limitations prevent setting NOT NULL constraint.")
                        print("   New projects will still require team_id, but existing ones are assigned to default team.")
                    else:
                        # No existing data, can add as NOT NULL
                        conn.execute(text("ALTER TABLE projects ADD COLUMN team_id INTEGER NOT NULL"))
                else:
                    # PostgreSQL approach: Add column with default value if there are existing projects
                    if project_count > 0:
                        conn.execute(text(f"""
                            ALTER TABLE projects 
                            ADD COLUMN team_id INTEGER NOT NULL DEFAULT {default_team_id}
                        """))
                        
                        # Remove the default constraint after setting values
                        conn.execute(text("ALTER TABLE projects ALTER COLUMN team_id DROP DEFAULT"))
                    else:
                        conn.execute(text("ALTER TABLE projects ADD COLUMN team_id INTEGER NOT NULL"))
                    
                    # Add foreign key constraint
                    conn.execute(text("""
                        ALTER TABLE projects 
                        ADD CONSTRAINT fk_projects_team_id 
                        FOREIGN KEY (team_id) REFERENCES teams(id)
                    """))
                
                print(" Successfully added team_id column to projects table")
                
                if project_count > 0:
                    print(f" Assigned {project_count} existing projects to default team (ID: {default_team_id})")
                
                # Verify the migration
                result = conn.execute(text("SELECT COUNT(*) FROM projects WHERE team_id IS NOT NULL"))
                updated_count = result.fetchone()[0]
                
                if updated_count == project_count:
                    print(f" Migration verification successful: {updated_count} projects have team_id")
                else:
                    print(f"  Migration verification warning: Only {updated_count} of {project_count} projects have team_id")
                
                trans.commit()
                return True
                
            except Exception as e:
                trans.rollback()
                raise e
        
    except SQLAlchemyError as e:
        print(f" Database error during migration: {e}")
        return False
    except Exception as e:
        print(f" Error during migration: {e}")
        return False

def main():
    """Main function to run the migration."""
    print("Migrating projects table to add team_id column...")
    print("=" * 60)
    
    success = migrate_projects_add_team_id()
    
    if success:
        print("\n Migration completed successfully!")
        print("\nChanges made:")
        print("1. Added team_id column to projects table")
        print("2. Assigned existing projects to default team (if any)")
        print("3. Added foreign key constraint (PostgreSQL)")
        print("\nNext steps:")
        print("1. Restart your FastAPI application")
        print("2. All new projects will require a team_id")
        print("3. Update your frontend to include team selection")
    else:
        print("\n Migration failed")
        print("Please check the error messages above and resolve any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
