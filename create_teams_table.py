#!/usr/bin/env python3
"""
Script to create the teams table in the database.
This script can be run manually to add the teams table to an existing database.
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base

def create_teams_table():
    """
    Create the teams table in the database.
    This function creates only the teams table without affecting other tables.
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
        
        # Import the models to ensure they're registered with Base
        from models import Team, TeamMember
        
        # Create the teams and team_members tables
        Team.__table__.create(bind=engine, checkfirst=True)
        TeamMember.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Teams and TeamMembers tables created successfully!")
        print("\nTeams table structure:")
        print("- id: Primary key (Integer)")
        print("- name: Team name (String, unique)")
        print("- description: Team description (String, optional)")
        print("- created_at: Creation timestamp (DateTime)")
        print("\nTeamMembers table structure:")
        print("- team_id: Foreign key to teams table (Integer, Primary Key)")
        print("- user_id: Foreign key to users table (Integer, Primary Key)")
        print("- role: Role within team (Enum: member, lead, admin)")
        print("- joined_at: Join timestamp (DateTime)")
        
        # Verify tables were created by checking if they exist
        with engine.connect() as conn:
            if database_url.startswith("sqlite"):
                teams_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'"))
                team_members_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='team_members'"))
            else:
                teams_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename='teams'"))
                team_members_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename='team_members'"))
            
            teams_exists = teams_result.fetchone() is not None
            team_members_exists = team_members_result.fetchone() is not None
            
            if teams_exists and team_members_exists:
                print("\n✅ Table verification successful - both teams and team_members tables exist in database")
            else:
                if not teams_exists:
                    print("\n❌ Table verification failed - teams table not found")
                if not team_members_exists:
                    print("\n❌ Table verification failed - team_members table not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating teams table: {e}")
        return False

def main():
    """Main function to run the script."""
    print("Creating teams table...")
    print("=" * 50)
    
    success = create_teams_table()
    
    if success:
        print("\n🎉 Teams and TeamMembers tables setup completed successfully!")
        print("\nYou can now:")
        print("1. Start your FastAPI application")
        print("2. Create teams via the API endpoints:")
        print("   - POST /teams/ (admin only)")
        print("   - POST /teams/{team_id}/members (admin only)")
        print("   - GET /teams/{team_id}/members")
        print("   - DELETE /teams/{team_id}/members/{user_id} (admin only)")
        print("3. Manage team memberships with role-based permissions")
    else:
        print("\n💥 Failed to create teams and team_members tables")
        sys.exit(1)

if __name__ == "__main__":
    main()
