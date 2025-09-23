"""
Users router handling user management operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, UserRole
from schemas import UserResponse
from routers.auth import get_current_user, get_current_admin_user

# Router instance
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users for task assignment purposes.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        List of all users (for task assignment)
    """
    # Allow all authenticated users to see all users for task assignment
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        User information
    
    Raises:
        HTTPException: If user not found or not authorized
    """
    # Users can only view their own profile unless they're admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user's information."
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.get("/{user_id}/teams")
def get_user_teams(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get teams that a user belongs to.
    
    Args:
        user_id: The ID of the user
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        List of teams the user belongs to (empty array if no teams)
    
    Raises:
        HTTPException: If user not found or not authorized
    """
    # Users can only view their own teams unless they're admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user's teams."
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's teams
    from models import Team, TeamMember
    from sqlalchemy.orm import joinedload
    
    teams = db.query(Team).join(TeamMember).filter(
        TeamMember.user_id == user_id
    ).options(joinedload(Team.team_memberships)).all()
    
    # Always return an array, even if empty - DO NOT return 404 for no teams
    return teams