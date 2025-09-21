"""
Pydantic schemas for request/response validation.
Using Pydantic v2 style with model_config and field_validator.
"""

from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional, List
from datetime import datetime
import re
from models import UserRole, TaskStatus

# User Schemas
class UserBase(BaseModel):
    """Base schema for User with common attributes"""
    email: str = Field(..., min_length=5, max_length=255, description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    role: UserRole = UserRole.MEMBER

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email format using regex pattern"""
        if not value:
            raise ValueError('Email is required')
        
        # Comprehensive email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        
        # Additional checks
        if value.count('@') != 1:
            raise ValueError('Email must contain exactly one @ symbol')
        
        local, domain = value.split('@')
        if len(local) > 64:
            raise ValueError('Email local part is too long')
        
        if len(domain) > 255:
            raise ValueError('Email domain is too long')
        
        return value.lower().strip()

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Validate username format"""
        if not value:
            raise ValueError('Username is required')
        
        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        
        return value.strip()

class UserCreate(UserBase):
    """Schema for creating a new user (signup)"""
    password: str = Field(..., min_length=8, max_length=128, description="Password")

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate password strength"""
        if not value:
            raise ValueError('Password is required')
        
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(value) > 128:
            raise ValueError('Password must be less than 128 characters')
        
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', value):
            raise ValueError('Password must contain at least one letter')
        
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one number')
        
        return value

class UserLogin(BaseModel):
    """Schema for user login"""
    email: str = Field(..., min_length=5, max_length=255, description="Valid email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email format using regex pattern"""
        if not value:
            raise ValueError('Email is required')
        
        # Comprehensive email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        
        return value.lower().strip()

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
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate project name"""
        if not value or not value.strip():
            raise ValueError('Project name is required')
        
        if len(value.strip()) < 1:
            raise ValueError('Project name cannot be empty')
        
        return value.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """Validate project description"""
        if value is not None:
            return value.strip() if value.strip() else None
        return value

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
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: TaskStatus = TaskStatus.TODO

    @field_validator('title')
    @classmethod
    def validate_title(cls, value: str) -> str:
        """Validate task title"""
        if not value or not value.strip():
            raise ValueError('Task title is required')
        
        if len(value.strip()) < 1:
            raise ValueError('Task title cannot be empty')
        
        return value.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """Validate task description"""
        if value is not None:
            return value.strip() if value.strip() else None
        return value

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
