"""
Projects router handling CRUD operations for projects.
Only authenticated users can manage projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models import Project, User, UserRole, Team, TeamMember
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithTasks
from routers.auth import get_current_user

# Router instance
router = APIRouter(prefix="/projects", tags=["Projects"])

def check_team_access(user: User, team_id: int, db: Session) -> Team:
    """
    Check if user has access to the specified team and return the team.
    
    Args:
        user: The authenticated user
        team_id: ID of the team to check
        db: Database session
        
    Returns:
        Team object if access is granted
        
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
    
    # Admins can access any team
    if user.role == UserRole.ADMIN:
        return team
    
    # Check if user is a member of the team
    team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id
    ).first()
    
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Access Denied",
                "message": f"You don't have access to team '{team.name}'",
                "field": "team_id"
            }
        )
    
    return team

@router.get("/", response_model=List[ProjectResponse])
def get_all_projects(
    skip: int = 0,
    limit: int = 100,
    team_id: int = None,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects with team-based access control.
    
    **Access Control:**
    - Admin users can see all projects
    - Regular users can only see projects from teams they belong to
    - Users must be team members to see team projects
    
    **Filtering:**
    - Optional team_id filter to get projects from specific team
    - Optional search filter to find projects by name or description
    
    Args:
        skip: Number of projects to skip (for pagination)
        limit: Maximum number of projects to return (max 100)
        team_id: Optional team ID to filter projects
        search: Optional search term to filter by project name or description
        current_user: The authenticated user
        db: Database session
    
    Returns:
        List of projects with team and creator information
        
    Raises:
        HTTPException: If team_id provided but user doesn't have access
    """
    # Enforce maximum limit for performance
    limit = min(limit, 100)
    
    # Build base query with joins
    query = db.query(Project).options(
        joinedload(Project.creator),
        joinedload(Project.team)
    )
    
    # Apply team-based access control
    if current_user.role == UserRole.ADMIN:
        # Admins can see all projects
        if team_id:
            # Verify team exists and apply filter
            check_team_access(current_user, team_id, db)
            query = query.filter(Project.team_id == team_id)
    else:
        # Regular users can only see projects from teams they belong to
        user_team_ids = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == current_user.id
        ).subquery()
        
        query = query.filter(Project.team_id.in_(user_team_ids))
        
        if team_id:
            # Verify user has access to the specific team and apply filter
            check_team_access(current_user, team_id, db)
            query = query.filter(Project.team_id == team_id)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            Project.name.ilike(search_term) | 
            Project.description.ilike(search_term)
        )
    
    # Apply pagination and execute query
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectWithTasks)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID, including all its tasks.
    
    Args:
        project_id: The ID of the project to retrieve
        current_user: The authenticated user
        db: Database session
    
    Returns:
        Project with tasks, team, and creator information
    
    Raises:
        HTTPException: If project not found or user doesn't have permission
    """
    # Find the project with related data
    project = db.query(Project).options(
        joinedload(Project.creator),
        joinedload(Project.team),
        joinedload(Project.tasks)
    ).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Project Not Found",
                "message": f"Project with ID {project_id} does not exist",
                "field": "project_id"
            }
        )
    
    # Check permissions: Admin can see all, team members can see team projects
    if current_user.role != UserRole.ADMIN:
        # Check if user is a member of the project's team
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Access Denied",
                    "message": "You don't have access to this project",
                    "field": "project_id"
                }
            )
    
    return project

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project.
    
    The authenticated user will be set as the project creator.
    User must have access to the specified team.
    
    Args:
        project: Project creation data (including team_id)
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The created project
        
    Raises:
        HTTPException: If team not found or user doesn't have access
    """
    # Verify user has access to the team
    team = check_team_access(current_user, project.team_id, db)
    
    # Create new project with current user as creator and specified team
    db_project = Project(
        name=project.name,
        description=project.description,
        creator_id=current_user.id,
        team_id=project.team_id
    )
    
    # Save to database
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a project.
    
    Only the project creator or an admin can update a project.
    
    Args:
        project_id: The ID of the project to update
        project_update: Updated project data
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The updated project
    
    Raises:
        HTTPException: If project not found or user doesn't have permission
    """
    # Find the project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions:
    # Admin can update any; otherwise user must be a member of the project's team
    if current_user.role != UserRole.ADMIN:
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
    
    # Update project fields if provided
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.team_id is not None:
        # Verify user has access to the new team
        new_team = check_team_access(current_user, project_update.team_id, db)
        project.team_id = project_update.team_id
    
    # Save changes
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project.
    
    Only the project creator or an admin can delete a project.
    This will also delete all tasks associated with the project.
    
    Args:
        project_id: The ID of the project to delete
        current_user: The authenticated user
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If project not found or user doesn't have permission
    """
    # Find the project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions:
    # Admin can delete any; otherwise user must be a member of the project's team
    if current_user.role != UserRole.ADMIN:
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this project"
            )
    
    # Delete the project (tasks will be deleted automatically due to cascade)
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}
