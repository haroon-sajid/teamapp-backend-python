"""
SQLAlchemy models for the Kanban Board application.
These models define the structure of our database tables.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# Enum for user roles
class UserRole(str, enum.Enum):
    """Enum defining user roles in the system"""
    ADMIN = "admin"
    MEMBER = "member"

# Enum for task status
class TaskStatus(str, enum.Enum):
    """Enum defining possible task statuses"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class User(Base):
    """
    User model representing users in the system.
    Each user has a unique email and can have either admin or member role.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User information
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Role can be either 'admin' or 'member'
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # A user can create many projects
    created_projects = relationship("Project", back_populates="creator", cascade="all, delete-orphan")
    # A user can be assigned to many tasks
    assigned_tasks = relationship("Task", back_populates="assignee")

class Project(Base):
    """
    Project model representing projects in the Kanban board.
    Each project belongs to a user (creator) and can have multiple tasks.
    """
    __tablename__ = "projects"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Project information
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Foreign key to User who created the project
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Link back to the user who created this project
    creator = relationship("User", back_populates="created_projects")
    # A project can have many tasks
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    """
    Task model representing tasks within projects.
    Each task belongs to a project and can be assigned to a user.
    """
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Task information
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Task can be unassigned
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Link back to the project this task belongs to
    project = relationship("Project", back_populates="tasks")
    # Link to the user assigned to this task (if any)
    assignee = relationship("User", back_populates="assigned_tasks")
