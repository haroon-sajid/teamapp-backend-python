"""
Authentication router handling user signup and login.
Uses JWT tokens for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import re

from database import get_db
from models import User, UserRole, Team, TeamMember, TeamMemberRole
from schemas import (
    UserCreate, UserResponse, Token, TokenData, UserLogin, UserLoginFlexible,
    PasswordChange, MessageResponse,
    RefreshTokenRequest
)

# Router instance
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security configuration - Secret key for JWT - configurable via environment
SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access token for security

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --------------------  NEW HELPER --------------------

def raise_http_error(
    status_code: int,
    error: str,
    message: str,
    field: Optional[str] = None
):
    """
    Helper to raise consistent HTTPExceptions with a standard JSON structure.
    """
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "error": error,
            "message": message,
            "field": field
        }
    )

# ------------------------------------------------------


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Decode JWT token and return the current user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise_http_error(status.HTTP_401_UNAUTHORIZED, "Invalid token", "Could not validate credentials")
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("role")
        )
    except JWTError:
        raise_http_error(status.HTTP_401_UNAUTHORIZED, "Invalid token", "Could not validate credentials")

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise_http_error(status.HTTP_401_UNAUTHORIZED, "Invalid user", "User not found")
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise_http_error(
            status.HTTP_403_FORBIDDEN,
            "Access denied",
            "You do not have permission to perform this action. Admin access is required."
        )
    return current_user



# -------------------- AUTH ROUTES -------------------- #

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account with validation."""

    if db.query(User).filter(User.email == user.email).first():
        raise_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Email already registered",
            "An account with this email already exists. Try logging in.",
            "email"
        )

    if db.query(User).filter(User.username == user.username).first():
        raise_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Username already taken",
            "This username is already taken. Please choose another.",
            "username"
        )

    password = user.password
    if len(password) < 8:
        raise_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Weak password",
            "Password must be at least 8 characters long.",
            "password"
        )

    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Weak password",
            "Password must include both letters and numbers.",
            "password"
        )

    hashed_password = get_password_hash(password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role or UserRole.MEMBER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    try:
        if not db.query(TeamMember).filter(TeamMember.user_id == db_user.id).first():
            personal_team = Team(name=f"{db_user.username}'s Team", description=f"Personal team for {db_user.username}")
            db.add(personal_team)
            db.commit()
            db.refresh(personal_team)
            membership = TeamMember(team_id=personal_team.id, user_id=db_user.id, role=TeamMemberRole.MEMBER)
            db.add(membership)
            db.commit()
    except Exception:
        db.rollback()

    return db_user


from schemas import UserLogin  # already imported in your file

@router.post("/login-email", response_model=Token)
def login_email(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password using proper Pydantic validation."""
    
    # Authenticate user
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise_http_error(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication Error",
            "Invalid email or password.",
        )

    # Create tokens
    token_data = {"user_id": user.id, "email": user.email, "role": user.role.value}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/debug-login")
def debug_login(data: UserLogin):
    """Debug endpoint to test if data is being received properly."""
    return {
        "success": True,
        "message": "Data received successfully",
        "received_email": data.email,
        "received_password_length": len(data.password),
        "email_type": type(data.email).__name__,
        "password_type": type(data.password).__name__
    }


@router.post("/login", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Alternative login endpoint that accepts form data (OAuth2 compatible)."""
    
    # Authenticate user - form_data.username can be email or username
    user = db.query(User).filter(
        or_(User.email == form_data.username.lower(), User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise_http_error(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication Error", 
            "Invalid email or password.",
        )

    # Create tokens
    token_data = {"user_id": user.id, "email": user.email, "role": user.role.value}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# (Reverted) OAuth2 form login removed per request

# ---------------- Other login endpoints ---------------- #
# (Same logic applies — all use raise_http_error now)
# -------------------------------------------------------


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Incorrect current password",
            "The current password you entered is incorrect. Please try again.",
            "current_password"
        )

    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return MessageResponse(message="Password has been successfully changed.", success=True)
