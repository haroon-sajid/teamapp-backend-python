"""
Tasks router handling CRUD operations for tasks.
Includes task assignment functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from database import get_db
from models import Task, User, Project, UserRole, TaskStatus, TeamMember
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
    Verify the current user can access the given project.

    Admins: access to all projects.
    Members: must belong to the team's project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if current_user.role != UserRole.ADMIN:
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )

    return project

@router.get("", response_model=List[TaskResponse])
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
    
    **Access Control:**
    - Admin users can see all tasks
    - Member users can only see tasks assigned to them from projects in their teams
    - If assigned_to_me is True, only show tasks assigned to current user
    
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
    
    # Apply access control based on user role
    if current_user.role == UserRole.ADMIN:
        # Admins can see all tasks
        if project_id:
            # Check project permission (admins can access any project)
            check_project_permission(project_id, current_user, db)
            query = query.filter(Task.project_id == project_id)
    else:
        # Member users can see tasks assigned to them (regardless of team/project)
        # This allows admins to assign tasks from any project to any user
        query = query.filter(Task.assignee_id == current_user.id)
        
        if project_id:
            # If a specific project is requested, also filter by project
            # But only if the user has tasks in that project
            query = query.filter(Task.project_id == project_id)
    
    # Apply additional filters
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
    
    **Access Control:**
    - Admin users can see any task
    - Member users can only see tasks assigned to them
    
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
    
    # Access control: Admins can see any task, Members can only see tasks assigned to them
    if current_user.role != UserRole.ADMIN and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view tasks assigned to you"
        )
    
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
    try:
        # Verify the project exists (basic validation)
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Ensure the user can access the project's team (403 if not)
        if current_user.role != UserRole.ADMIN:
            team_member = db.query(TeamMember).filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == current_user.id
            ).first()
            if not team_member:
                # Log minimal helpful context
                try:
                    print(f"🚫 Task create denied: user_id={current_user.id} project_id={task.project_id} team_id={project.team_id}")
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to create tasks for this project"
                )
        
        # Check assignment permissions
        if task.assignee_id is not None:
            # Verify the assignee exists
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        # Create new task
        db_task = Task(
            title=task.title,
            description=task.description,
            status=task.status,
            project_id=task.project_id,
            assignee_id=task.assignee_id
        )
        
        # Save to database
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return db_task
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f" Error creating task: {str(e)}")
        print(f" Task data: {task}")
        print(f" Current user: {current_user.id}")
        import traceback
        print(f" Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating task"
        )

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a task.
    
    **Access Control:**
    - Admin users can update any task
    - Member users can only update tasks assigned to them
    
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
    
    # Access control: Admins can update any task, Members can only update tasks assigned to them
    if current_user.role != UserRole.ADMIN and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update tasks assigned to you"
        )
    
    # Check assignment permissions if assignee is being updated
    if task_update.assignee_id is not None:
        # Verify the assignee exists
        assignee = db.query(User).filter(User.id == task_update.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    # Update task fields if provided
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.assignee_id is not None:
        task.assignee_id = task_update.assignee_id
    
    # Save changes
    db.commit()
    db.refresh(task)
    
    return task

@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update only the status of a task.
    
    **Access Control:**
    - Admin users can update any task status
    - Member users can only update status of tasks assigned to them
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Access control: Admins can update any task status, Members can only update tasks assigned to them
    if current_user.role != UserRole.ADMIN and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update status of tasks assigned to you"
        )

    # Validate presence of status in request body
    if task_update.status is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'status' is required"
        )

    task.status = task_update.status
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
    
    **Access Control:**
    - Only admin users can delete tasks
    - Member users cannot delete tasks
    
    Args:
        task_id: The ID of the task to delete
        current_user: The authenticated user
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If task not found or user doesn't have permission
    """
    # Only admins can delete tasks
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tasks"
        )
    
    # Find the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # No additional project permission check needed for deletion - admin-only operation
    
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
    
    # For task assignment, only check if user has permission to assign tasks (admin or task creator)
    
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
    
    # For task assignment, only check if user has permission to assign tasks (admin or task creator)
    
    # Remove assignment
    task.assignee_id = None
    
    # Save changes
    db.commit()
    db.refresh(task)
    
    return task
