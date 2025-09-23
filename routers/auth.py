"""
Authentication router handling user signup and login.
Uses JWT tokens for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from database import get_db
from models import User, UserRole
from schemas import (
    UserCreate, UserResponse, Token, TokenData, UserLogin, UserLoginFlexible,
    PasswordChange, MessageResponse,
    RefreshTokenRequest
)

# Router instance
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security configuration
# Secret key for JWT - configurable via environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access token for security

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user information
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing user information
    
    Returns:
        Encoded JWT refresh token as string
    """
    to_encode = data.copy()
    # Refresh token expires in 7 days
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Decode JWT token and return the current user.
    
    This function is used as a dependency in protected routes.
    
    Args:
        token: JWT token from the request header
        db: Database session
    
    Returns:
        Current User object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
        # Create token data object
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("role")
        )
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is an admin.
    Use this dependency for admin-only routes.
    
    Args:
        current_user: The current authenticated user
    
    Returns:
        Current User object if admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user

# API Endpoints
@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    Args:
        user: User creation data (email, username, password, role)
        db: Database session
    
    Returns:
        Created user information (without password)
    
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Email already registered",
                "message": "An account with this email address already exists. Please use a different email or try logging in.",
                "field": "email"
            }
        )
    
    # Check if user with this username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Username already taken",
                "message": "This username is already taken. Please choose a different username.",
                "field": "username"
            }
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role or UserRole.MEMBER
    )
    
    # Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with username and password.
    
    OAuth2 compatible login endpoint.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # OAuth2 spec requires 'username' field, but we'll accept email
    # Try to find user by email first, then by username
    user = db.query(User).filter(
        or_(User.email == form_data.username, User.username == form_data.username)
    ).first()
    
    # Verify user exists and password is correct
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "User not found",
                "message": "No account found with this email or username. Please check your credentials or sign up for a new account.",
                "field": "username"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Incorrect password",
                "message": "The password you entered is incorrect. Please try again.",
                "field": "password"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

@router.post("/login/json", response_model=Token)
def login_json(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Alternative login endpoint that accepts JSON.
    
    This is easier to use with tools like curl or Postman.
    
    Args:
        user_credentials: Email and password in JSON format
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    # Verify user exists and password is correct
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "User not found",
                "message": "No account found with this email address. Please check your email or sign up for a new account.",
                "field": "email"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Incorrect password",
                "message": "The password you entered is incorrect. Please try again.",
                "field": "password"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

@router.post("/login-email", response_model=Token)
def login_email(user_credentials: UserLoginFlexible, db: Session = Depends(get_db)):
    """
    Login endpoint that accepts email or username in JSON format.
    
    This endpoint is designed for frontend applications and accepts both
    email addresses and usernames for login.
    
    Args:
        user_credentials: Email/username and password in JSON format
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Try to find user by email first, then by username
    user = db.query(User).filter(
        or_(User.email == user_credentials.email_or_username, User.username == user_credentials.email_or_username)
    ).first()
    
    # Verify user exists and password is correct
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "User not found",
                "message": "No account found with this email or username. Please check your credentials or sign up for a new account.",
                "field": "email_or_username"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Incorrect password",
                "message": "The password you entered is incorrect. Please try again.",
                "field": "password"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

@router.post("/login-username", response_model=Token)
def login_username(user_credentials: UserLoginFlexible, db: Session = Depends(get_db)):
    """
    Login endpoint that accepts email or username in JSON format.
    
    This is an alias for /login-email for backward compatibility.
    Both endpoints work identically and accept both email and username.
    
    Args:
        user_credentials: Email/username and password in JSON format
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Delegate to the main flexible login endpoint
    return login_email(user_credentials, db)

@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: The refresh token
        db: Database session
    
    Returns:
        New access and refresh tokens
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Invalid refresh token",
            "message": "The refresh token is invalid or has expired. Please log in again.",
            "field": "refresh_token"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the refresh token
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }
    
    new_access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

@router.post("/logout", response_model=MessageResponse)
def logout():
    """
    Logout endpoint.
    
    In a stateless JWT system, logout is handled on the client side
    by removing the token from storage. This endpoint exists for
    consistency and future enhancements (like token blacklisting).
    
    Returns:
        Success message
    """
    return MessageResponse(
        message="Successfully logged out. Please remove the token from your client storage.",
        success=True
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    This is a protected route that requires authentication.
    
    Args:
        current_user: The current authenticated user (from token)
    
    Returns:
        Current user information
    """
    return current_user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: PasswordChange, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    Args:
        request: Current password and new password
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Incorrect current password",
                "message": "The current password you entered is incorrect. Please try again.",
                "field": "current_password"
            }
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return MessageResponse(
        message="Password has been successfully changed.",
        success=True
    )
