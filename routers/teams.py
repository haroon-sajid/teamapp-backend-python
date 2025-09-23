"""
Teams router for team management endpoints.
Provides CRUD operations for teams and team membership management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import Team, TeamMember, User, UserRole, TeamMemberRole
from schemas import (
    TeamCreate, TeamResponse, TeamWithMembers, TeamMemberAdd, 
    TeamMemberResponse, MessageResponse, UserResponse
)
from routers.auth import get_current_user

router = APIRouter(
    prefix="/teams",
    tags=["teams"],
    responses={404: {"description": "Not found"}},
)

def check_admin_permission(current_user: User):
    """
    Check if the current user has admin permissions.
    
    Args:
        current_user: The authenticated user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Insufficient Permissions",
                "message": "Only administrators can perform this action",
                "field": "role"
            }
        )

def check_team_access_permission(current_user: User, team_id: int, db: Session):
    """
    Check if the current user can access team information.
    Admins can access any team, team members can access their own teams.
    
    Args:
        current_user: The authenticated user
        team_id: ID of the team to check access for
        db: Database session
        
    Raises:
        HTTPException: If user doesn't have access to the team
    """
    if current_user.role == UserRole.ADMIN:
        return  # Admins can access any team
    
    # Check if user is a member of the team
    team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Access Denied",
                "message": "You don't have access to this team",
                "field": "team_id"
            }
        )


@router.post("", response_model=TeamWithMembers, status_code=status.HTTP_201_CREATED)
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new team (Admin only).
    
    Args:
        team: Team creation data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created team information
        
    Raises:
        HTTPException: If user is not admin or team name already exists
    """
    # Check admin permission
    check_admin_permission(current_user)
    
    # Check if team name already exists
    existing_team = db.query(Team).filter(Team.name == team.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Team Already Exists",
                "message": f"A team with the name '{team.name}' already exists",
                "field": "name"
            }
        )
    
    # Create new team
    db_team = Team(
        name=team.name,
        description=team.description
    )
    
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # Add members to the team if member_ids provided
    if team.member_ids:
        for user_id in team.member_ids:
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue  # Skip non-existent users
            
            # Check if user is already a member
            existing_membership = db.query(TeamMember).filter(
                TeamMember.team_id == db_team.id,
                TeamMember.user_id == user_id
            ).first()
            
            if not existing_membership:
                # Add user as a member
                team_member = TeamMember(
                    team_id=db_team.id,
                    user_id=user_id,
                    role=TeamMemberRole.MEMBER
                )
                db.add(team_member)
        
        # Commit the member additions
        db.commit()
    
    # Return team with members loaded
    team_with_members = db.query(Team).options(
        joinedload(Team.team_memberships).joinedload(TeamMember.user)
    ).filter(Team.id == db_team.id).first()
    
    return team_with_members


@router.get("", response_model=List[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all teams.
    Admins can see all teams, regular users can see teams they're members of.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of teams
    """
    if current_user.role == UserRole.ADMIN:
        # Admins can see all teams
        teams = db.query(Team).all()
    else:
        # Regular users can only see teams they're members of
        teams = db.query(Team).join(TeamMember).filter(
            TeamMember.user_id == current_user.id
        ).all()
    
    return teams

@router.get("/{team_id}", response_model=TeamWithMembers)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get team details with members.
    
    Args:
        team_id: ID of the team
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Team details with members
        
    Raises:
        HTTPException: If team not found or user doesn't have access
    """
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Team Not Found",
                "message": f"Team with ID {team_id} does not exist",
                "field": "team_id"
            }
        )
    
    # Check access permission
    check_team_access_permission(current_user, team_id, db)
    
    # Get team with members
    team_with_members = db.query(Team).options(
        joinedload(Team.team_memberships).joinedload(TeamMember.user)
    ).filter(Team.id == team_id).first()
    
    return team_with_members

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a member to a team (Admin only).
    
    Args:
        team_id: ID of the team
        member_data: Member data including user_id and role
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created team membership information
        
    Raises:
        HTTPException: If user is not admin, team not found, user not found, or user already in team
    """
    # Check admin permission
    check_admin_permission(current_user)
    
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Team Not Found",
                "message": f"Team with ID {team_id} does not exist",
                "field": "team_id"
            }
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User Not Found",
                "message": f"User with ID {member_data.user_id} does not exist",
                "field": "user_id"
            }
        )
    
    # Check if user is already a member of the team
    existing_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == member_data.user_id
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "User Already in Team",
                "message": f"User '{user.username}' is already a member of team '{team.name}'",
                "field": "user_id"
            }
        )
    
    # Create team membership
    team_member = TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    db.add(team_member)
    db.commit()
    db.refresh(team_member)
    
    # Get the team member with user details for response
    team_member_with_user = db.query(TeamMember).options(
        joinedload(TeamMember.user)
    ).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == member_data.user_id
    ).first()
    
    return team_member_with_user

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all members of a team.
    Admins can see members of any team, team members can see their own team members.
    
    Args:
        team_id: ID of the team
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of team members
        
    Raises:
        HTTPException: If team not found or user doesn't have access
    """
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Team Not Found",
                "message": f"Team with ID {team_id} does not exist",
                "field": "team_id"
            }
        )
    
    # Check access permission
    check_team_access_permission(current_user, team_id, db)
    
    # Get team members with user details
    team_members = db.query(TeamMember).options(
        joinedload(TeamMember.user)
    ).filter(TeamMember.team_id == team_id).all()
    
    return team_members

@router.delete("/{team_id}/members/{user_id}", response_model=MessageResponse)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a member from a team (Admin only).
    
    Args:
        team_id: ID of the team
        user_id: ID of the user to remove
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user is not admin, team not found, user not found, or user not in team
    """
    # Check admin permission
    check_admin_permission(current_user)
    
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Team Not Found",
                "message": f"Team with ID {team_id} does not exist",
                "field": "team_id"
            }
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User Not Found",
                "message": f"User with ID {user_id} does not exist",
                "field": "user_id"
            }
        )
    
    # Check if user is a member of the team
    team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User Not in Team",
                "message": f"User '{user.username}' is not a member of team '{team.name}'",
                "field": "user_id"
            }
        )
    
    # Remove team membership
    db.delete(team_member)
    db.commit()
    
    return MessageResponse(
        message=f"User '{user.username}' has been removed from team '{team.name}'",
        success=True
    )

@router.delete("/{team_id}", response_model=MessageResponse)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a team (Admin only).
    This will also remove all team memberships.
    
    Args:
        team_id: ID of the team to delete
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user is not admin or team not found
    """
    # Check admin permission
    check_admin_permission(current_user)
    
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Team Not Found",
                "message": f"Team with ID {team_id} does not exist",
                "field": "team_id"
            }
        )
    
    team_name = team.name
    
    # Delete team (cascade will handle team memberships)
    db.delete(team)
    db.commit()
    
    return MessageResponse(
        message=f"Team '{team_name}' has been deleted successfully",
        success=True
    )
