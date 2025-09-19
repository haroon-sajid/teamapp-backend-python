"""
Pydantic schemas for request/response validation.
Using Pydantic v2 style with model_config.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import UserRole, TaskStatus

# User Schemas
class UserBase(BaseModel):
    """Base schema for User with common attributes"""
    email: EmailStr
    username: str
    role: UserRole = UserRole.MEMBER

class UserCreate(UserBase):
    """Schema for creating a new user (signup)"""
    password: str

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """Schema for user response (excludes password)"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data stored in JWT token"""
    user_id: int
    email: str
    role: UserRole

# Project Schemas
class ProjectBase(BaseModel):
    """Base schema for Project with common attributes"""
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""
    pass  # Inherits everything from ProjectBase

class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)"""
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: int
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator: UserResponse  # Include creator details
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class ProjectWithTasks(ProjectResponse):
    """Schema for project response including tasks"""
    tasks: List['TaskResponse'] = []

# Task Schemas
class TaskBase(BaseModel):
    """Base schema for Task with common attributes"""
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO

class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    project_id: int

class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None  # Include assignee details if assigned
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class TaskAssign(BaseModel):
    """Schema for assigning a task to a user"""
    user_id: int

# Update forward references
ProjectWithTasks.model_rebuild()
