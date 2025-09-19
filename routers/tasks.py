"""
Tasks router handling CRUD operations for tasks.
Includes task assignment functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Task, User, Project, UserRole, TaskStatus
from schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssign
from routers.auth import get_current_user

# Router instance
router = APIRouter(prefix="/tasks", tags=["Tasks"])

def check_project_permission(
    project_id: int,
    current_user: User,
    db: Session
) -> Project:
    """
    Helper function to check if user has permission to access a project.
    
    Args:
        project_id: The ID of the project
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The project if user has permission
    
    Raises:
        HTTPException: If project not found or user doesn't have permission
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions: Admin can access all, others can only access their own
    if current_user.role != UserRole.ADMIN and project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    return project

@router.get("/", response_model=List[TaskResponse])
def get_all_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    assigned_to_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all tasks with optional filters.
    
    Args:
        skip: Number of tasks to skip (for pagination)
        limit: Maximum number of tasks to return
        project_id: Filter by project ID (optional)
        status: Filter by task status (optional)
        assigned_to_me: If true, only show tasks assigned to current user
        current_user: The authenticated user
        db: Database session
    
    Returns:
        List of tasks
    """
    # Start with base query
    query = db.query(Task)
    
    # Apply filters
    if project_id:
        # Check project permission
        check_project_permission(project_id, current_user, db)
        query = query.filter(Task.project_id == project_id)
    elif current_user.role != UserRole.ADMIN:
        # Non-admin users can only see tasks from their projects
        user_projects = db.query(Project.id).filter(
            Project.creator_id == current_user.id
        ).subquery()
        query = query.filter(Task.project_id.in_(user_projects))
    
    if status:
        query = query.filter(Task.status == status)
    
    if assigned_to_me:
        query = query.filter(Task.assignee_id == current_user.id)
    
    # Execute query with pagination
    tasks = query.offset(skip).limit(limit).all()
    
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific task by ID.
    
    Args:
        task_id: The ID of the task to retrieve
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The task
    
    Raises:
        HTTPException: If task not found or user doesn't have permission
    """
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    return task

@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new task in a project.
    
    Args:
        task: Task creation data
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The created task
    
    Raises:
        HTTPException: If project not found or user doesn't have permission
    """
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    # Create new task
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        project_id=task.project_id
    )
    
    # Save to database
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a task.
    
    Args:
        task_id: The ID of the task to update
        task_update: Updated task data
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The updated task
    
    Raises:
        HTTPException: If task not found or user doesn't have permission
    """
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    # Update task fields if provided
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        task.status = task_update.status
    
    # Save changes
    db.commit()
    db.refresh(task)
    
    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a task.
    
    Args:
        task_id: The ID of the task to delete
        current_user: The authenticated user
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If task not found or user doesn't have permission
    """
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    # Delete the task
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@router.post("/{task_id}/assign/{user_id}", response_model=TaskResponse)
def assign_task(
    task_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a task to a user.
    
    Args:
        task_id: The ID of the task to assign
        user_id: The ID of the user to assign the task to
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The updated task with assignment
    
    Raises:
        HTTPException: If task/user not found or user doesn't have permission
    """
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    # Find the user to assign to
    assignee = db.query(User).filter(User.id == user_id).first()
    
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Assign the task
    task.assignee_id = user_id
    
    # Save changes
    db.commit()
    db.refresh(task)
    
    return task

@router.post("/{task_id}/unassign", response_model=TaskResponse)
def unassign_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove assignment from a task.
    
    Args:
        task_id: The ID of the task to unassign
        current_user: The authenticated user
        db: Database session
    
    Returns:
        The updated task without assignment
    
    Raises:
        HTTPException: If task not found or user doesn't have permission
    """
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check project permission
    check_project_permission(task.project_id, current_user, db)
    
    # Remove assignment
    task.assignee_id = None
    
    # Save changes
    db.commit()
    db.refresh(task)
    
    return task
