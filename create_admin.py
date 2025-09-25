#!/usr/bin/env python3
"""
Script to create an admin user for testing purposes.
Run this script to create an admin user that can access settings and manage the application.
"""

import os
import sys
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    """Create an admin user for testing purposes."""
    
    # Get database session
    db: Session = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@teamapp.com").first()
        
        if existing_admin:
            print("Admin user already exists.")
            print(f"Email: {existing_admin.email}")
            print(f"Username: {existing_admin.username}")
            print(f"Role: {existing_admin.role}")
            print("No changes were made.")
            return
        
        # Hash the password
        hashed_password = pwd_context.hash("admin123")
        
        # Create admin user
        admin_user = User(
            email="admin@teamapp.com",
            username="admin",
            hashed_password=hashed_password,
            role=UserRole.ADMIN
        )
        
        # Save to database
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin user created successfully.")
        print("=" * 40)
        print(f"Email: {admin_user.email}")
        print(f"Username: {admin_user.username}")
        print(f"Temporary password: admin123 (please change this immediately)")
        print(f"Role: {admin_user.role}")
        print(f"ID: {admin_user.id}")
        print("=" * 40)
        print("You can now log in with these credentials and access Settings.")
        
    except Exception as e:
        print(f"An error occurred while creating the admin user: {e}")
        db.rollback()
    finally:
        db.close()

def list_users():
    """List all users in the database."""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"Found {len(users)} user(s):")
        print("=" * 60)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Role: {user.role}")
            print(f"Created: {user.created_at}")
            print("-" * 30)
            
    except Exception as e:
        print(f"An error occurred while listing users: {e}")
    finally:
        db.close()

def promote_user_to_admin(email: str):
    """Promote an existing user to admin role."""
    db: Session = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"User with email '{email}' was not found.")
            return
        
        if user.role == UserRole.ADMIN:
            print(f"User '{email}' is already an administrator.")
            return
        
        # Update role to admin
        user.role = UserRole.ADMIN
        db.commit()
        
        print(f"User '{email}' has been promoted to administrator.")
        print(f"Username: {user.username}")
        print(f"New role: {user.role}")
        
    except Exception as e:
        print(f"An error occurred while promoting the user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage users in the Team Collaboration App")
    parser.add_argument("--create-admin", action="store_true", help="Create a default admin user")
    parser.add_argument("--list-users", action="store_true", help="List all users")
    parser.add_argument("--promote", type=str, help="Promote user with given email to admin")
    
    args = parser.parse_args()
    
    if args.create_admin:
        create_admin_user()
    elif args.list_users:
        list_users()
    elif args.promote:
        promote_user_to_admin(args.promote)
    else:
        print("Usage:")
        print("  python create_admin.py --create-admin     # Create default admin user")
        print("  python create_admin.py --list-users       # List all users")
        print("  python create_admin.py --promote EMAIL    # Promote user to admin")
        print("")
        print("Examples:")
        print("  python create_admin.py --create-admin")
        print("  python create_admin.py --promote user@example.com")
