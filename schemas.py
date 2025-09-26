"""
Pydantic schemas for request/response validation.
Using Pydantic v2 style with model_config and field_validator.
"""

from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional, List
from datetime import datetime
import re
from models import UserRole, TaskStatus, TeamMemberRole

# User Schemas
class UserBase(BaseModel):
    """Base schema for User with common attributes"""
    email: str = Field(
        ..., 
        min_length=5, 
        max_length=255, 
        description="Valid email address",
        examples=["user@example.com", "john.doe@gmail.com", "admin@company.com"]
    )
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="Username (3-50 characters, letters, numbers, underscores, hyphens)",
        examples=["john_doe", "user123", "admin-user", "testuser"]
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        description="User role in the system",
        examples=["member", "admin", "moderator"]
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email format using regex pattern"""
        if not value:
            raise ValueError('Please enter your email address')
        
        # Comprehensive email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise ValueError('Please enter a valid email address (e.g., user@example.com)')
        
        # Additional checks
        if value.count('@') != 1:
            raise ValueError('Email must contain exactly one @ symbol')
        
        local, domain = value.split('@')
        if len(local) > 64:
            raise ValueError('Email address is too long. Please use a shorter email address.')
        
        if len(domain) > 255:
            raise ValueError('Email domain is too long. Please use a different email address.')
        
        return value.lower().strip()

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Validate username format"""
        if not value:
            raise ValueError('Please enter a username')
        
        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        
        return value.strip()

class UserCreate(UserBase):
    """Schema for creating a new user (signup)"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="Password (minimum 8 characters, must contain letters and numbers)",
        examples=["mypassword123", "securepass456", "userpass789"]
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate password strength"""
        if not value:
            raise ValueError('Please enter a password')
        
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(value) > 128:
            raise ValueError('Password is too long. Please use a shorter password (less than 128 characters)')
        
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', value):
            raise ValueError('Password must contain at least one letter')
        
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one number')
        
        return value

class UserLogin(BaseModel):
    """Schema for user login."""
    # Accept multiple possible front-end keys via aliases for production compatibility
    email: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Your email address",
        examples=["user@example.com", "john.doe@gmail.com"],
        alias="emailOrUsername"
    )
    password: str = Field(
        ..., 
        min_length=1, 
        description="Your password",
        examples=["mypassword123", "securepass456"]
    )

    # Allow population by field name or alias (emailOrUsername)
    model_config = ConfigDict(populate_by_name=True)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email format using regex pattern"""
        if not value or not value.strip():
            raise ValueError('Email is required')
        
        # Comprehensive email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value.strip()):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        
        return value.lower().strip()

class UserLoginFlexible(BaseModel):
    """Schema for flexible user login (accepts email or username)"""
    email_or_username: str = Field(
        ..., 
        min_length=3, 
        max_length=255, 
        description="Your email address or username",
        examples=["user@example.com", "john_doe", "admin-user"]
    )
    password: str = Field(
        ..., 
        min_length=1, 
        description="Your password",
        examples=["mypassword123", "securepass456"]
    )

    @field_validator('email_or_username')
    @classmethod
    def validate_email_or_username(cls, value: str) -> str:
        """Validate email or username format"""
        if not value:
            raise ValueError('Email or username is required')
        
        # Check if it looks like an email (contains @)
        if '@' in value:
            # Validate as email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValueError('Invalid email format. Please provide a valid email address.')
            return value.lower().strip()
        else:
            # Validate as username
            if not re.match(r'^[a-zA-Z0-9_-]+$', value):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            return value.strip()

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
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 60 minutes in seconds

class TokenData(BaseModel):
    """Schema for data stored in JWT token"""
    user_id: int
    email: str
    role: UserRole

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="The refresh token")

# Project Schemas
class ProjectBase(BaseModel):
    """Base schema for Project with common attributes"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Project name",
        examples=["My Awesome Project", "Website Redesign", "Mobile App Development", "Data Analysis"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Project description (optional)",
        examples=["A comprehensive web application for team collaboration", "Redesigning the company website with modern UI/UX", "Building a mobile app for iOS and Android"]
    )

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
    team_id: int = Field(
        ..., 
        alias="teamId",
        description="ID of the team this project belongs to",
        examples=[1, 2, 3, 5]
    )
    
    # Pydantic v2 configuration
    model_config = ConfigDict(populate_by_name=True)

class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)"""
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = Field(
        None, 
        alias="teamId",
        description="ID of the team this project belongs to",
        examples=[1, 2, 3, 5]
    )
    
    # Pydantic v2 configuration
    model_config = ConfigDict(populate_by_name=True)

class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: int
    creator_id: int
    team_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator: Optional[UserResponse] = None  # Include creator details (optional for robustness)
    team: Optional['TeamResponse'] = None   # Include team details (optional for robustness)
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class ProjectWithTasks(ProjectResponse):
    """Schema for project response including tasks"""
    tasks: List['TaskResponse'] = []

# Task Schemas
class TaskBase(BaseModel):
    """Base schema for Task with common attributes"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200, 
        description="Task title",
        examples=["Design user interface", "Implement authentication", "Write unit tests", "Deploy to production", "Fix bug in login"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Task description (optional)",
        examples=["Create responsive design for mobile and desktop", "Add JWT token authentication with refresh tokens", "Write comprehensive test coverage for all endpoints", "Deploy the application to production environment"]
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Task status",
        examples=["todo", "in_progress", "done"]
    )

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
    project_id: int = Field(
        ..., 
        alias="projectId",
        description="ID of the project this task belongs to",
        examples=[1, 2, 3, 5]
    )
    assignee_id: Optional[int] = Field(
        None,
        alias="assigneeId", 
        description="ID of the user to assign this task to (optional)",
        examples=[1, 2, 3, 5, None]
    )

    # Pydantic v2 configuration
    model_config = ConfigDict(populate_by_name=True)

class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200, 
        description="Updated task title",
        examples=["Updated task title", "Fixed: Design user interface", "Completed: Implement authentication"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Updated task description",
        examples=["Updated description with more details", "Added implementation notes", "Completed with additional features"]
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Updated task status",
        examples=["todo", "in_progress", "done"]
    )
    assignee_id: Optional[int] = Field(
        None,
        alias="assigneeId", 
        description="ID of the user to assign this task to (optional, set to null to unassign)",
        examples=[1, 2, 3, 5, None]
    )

    # Pydantic v2 configuration
    model_config = ConfigDict(populate_by_name=True)

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
    user_id: int = Field(
        ..., 
        description="ID of the user to assign the task to",
        examples=[1, 2, 3, 5, 10]
    )


class PasswordChange(BaseModel):
    """Schema for changing password (requires current password)"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="New password (minimum 8 characters, must contain letters and numbers)",
        examples=["newpassword123", "securepass456", "changepass789"]
    )

    @field_validator('new_password')
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

# Team Schemas
class TeamBase(BaseModel):
    """Base schema for Team with common attributes"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Team name",
        examples=["Development Team", "Marketing Team", "QA Team", "Design Team"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Team description (optional)",
        examples=["Backend development team", "Product marketing team", "Quality assurance team"]
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate team name"""
        if not value or not value.strip():
            raise ValueError('Team name is required')
        
        if len(value.strip()) < 1:
            raise ValueError('Team name cannot be empty')
        
        return value.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """Validate team description"""
        if value is not None:
            return value.strip() if value.strip() else None
        return value

class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    member_ids: Optional[List[int]] = Field(
        None,
        description="List of user IDs to add as team members",
        examples=[[1, 2, 3], [5, 8]]
    )

class TeamUpdate(BaseModel):
    """Schema for updating a team (all fields optional)"""
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100, 
        description="Updated team name"
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Updated team description"
    )

class TeamMemberBase(BaseModel):
    """Base schema for TeamMember with common attributes"""
    role: TeamMemberRole = Field(
        default=TeamMemberRole.MEMBER,
        description="Role of the user within the team",
        examples=["member", "lead", "admin"]
    )

class TeamMemberAdd(TeamMemberBase):
    """Schema for adding a member to a team"""
    user_id: int = Field(
        ..., 
        description="ID of the user to add to the team",
        examples=[1, 2, 3, 5]
    )

class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""
    user_id: int
    team_id: int
    joined_at: datetime
    user: UserResponse  # Include user details
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class TeamResponse(TeamBase):
    """Schema for team response"""
    id: int
    created_at: datetime
    
    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

class TeamWithMembers(TeamResponse):
    """Schema for team response including members"""
    members: List[TeamMemberResponse] = []

class TeamWithProjects(TeamResponse):
    """Schema for team response including projects"""
    projects: List['ProjectResponse'] = []

class TeamWithMembersAndProjects(TeamResponse):
    """Schema for team response including both members and projects"""
    members: List[TeamMemberResponse] = []
    projects: List['ProjectResponse'] = []

# Response Schemas
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Whether the operation was successful")

# Update forward references
ProjectWithTasks.model_rebuild()
TeamWithMembers.model_rebuild()
TeamWithProjects.model_rebuild()
TeamWithMembersAndProjects.model_rebuild()
ProjectResponse.model_rebuild()
