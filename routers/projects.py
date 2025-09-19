"""
Projects router handling CRUD operations for projects.
Only authenticated users can manage projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Project, User, UserRole
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithTasks
from routers.auth import get_current_user

# Router instance
router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/", response_model=List[ProjectResponse])
def get_all_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects.
    
    - Admin users can see all projects
    - Regular users can only see their own projects
    
    Args:
        skip: Number of projects to skip (for pagination)
        limit: Maximum number of projects to return
        current_user: The authenticated user
        db: Database session
    
    Returns:
        List of projects
    """
    if current_user.role == UserRole.ADMIN:
        # Admins can see all projects
        projects = db.query(Project).offset(skip).limit(limit).all()
    else:
        # Regular users can only see their own projects
        projects = db.query(Project).filter(
            Project.creator_id == current_user.id
        ).offset(skip).limit(limit).all()
    
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
        Project with tasks
    
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
    
    # Check permissions: Admin can see all, others can only see their own
    if current_user.role != UserRole.ADMIN and project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this project"
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
    
    Args:
        project: Project creation data
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The created project
    """
    # Create new project with current user as creator
    db_project = Project(
        name=project.name,
        description=project.description,
        creator_id=current_user.id
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
    
    # Check permissions: Admin or project creator can update
    if current_user.role != UserRole.ADMIN and project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Update project fields if provided
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    
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
    
    # Check permissions: Admin or project creator can delete
    if current_user.role != UserRole.ADMIN and project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this project"
        )
    
    # Delete the project (tasks will be deleted automatically due to cascade)
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}
