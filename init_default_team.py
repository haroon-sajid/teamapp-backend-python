#!/usr/bin/env python3
"""
Database initialization script to create default team and admin user.
This script ensures the database has the necessary data for the application to work.
"""

import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User, Team, TeamMember, UserRole, TeamMemberRole
from routers.auth import get_password_hash

def create_default_team_and_admin():
    """Create a default team and admin user if they don't exist."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@teamapp.com").first()
        
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                email="admin@teamapp.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f" Admin user created with ID: {admin_user.id}")
        else:
            print(f" Admin user already exists with ID: {admin_user.id}")
        
        # Check if default team exists
        default_team = db.query(Team).filter(Team.name == "Default Team").first()
        
        if not default_team:
            print("Creating default team...")
            default_team = Team(
                name="Default Team",
                description="Default team for all users"
            )
            db.add(default_team)
            db.commit()
            db.refresh(default_team)
            print(f" Default team created with ID: {default_team.id}")
        else:
            print(f" Default team already exists with ID: {default_team.id}")
        
        # Check if admin is a member of the default team
        team_membership = db.query(TeamMember).filter(
            TeamMember.team_id == default_team.id,
            TeamMember.user_id == admin_user.id
        ).first()
        
        if not team_membership:
            print("Adding admin to default team...")
            team_membership = TeamMember(
                team_id=default_team.id,
                user_id=admin_user.id,
                role=TeamMemberRole.ADMIN
            )
            db.add(team_membership)
            db.commit()
            print(" Admin added to default team")
        else:
            print(" Admin is already a member of the default team")
        
        print("\n Database initialization completed successfully!")
        print(f" Admin email: admin@teamapp.com")
        print(f" Admin password: admin123")
        print(f" Default team: {default_team.name} (ID: {default_team.id})")
        
    except Exception as e:
        print(f" Error during initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print(" Initializing database with default team and admin user...")
    create_default_team_and_admin()
