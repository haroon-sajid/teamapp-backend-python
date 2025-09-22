"""
Main FastAPI application entry point.
This file sets up the FastAPI app and includes all routers.
"""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Import database components
from database import engine, Base

# Import routers
from routers import auth, projects, tasks

# Create database tables
# This will create all tables defined in models.py if they don't exist
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title="Kanban Board API",
    description="A simple and beginner-friendly Kanban board backend built with FastAPI",
    version="1.0.0"
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return user-friendly messages.
    """
    errors = []
    
    for error in exc.errors():
        field = error.get('loc', ['unknown'])[-1]  # Get the field name
        error_type = error.get('type', '')
        error_msg = error.get('msg', '')
        
        # Create user-friendly error messages
        if field == 'email':
            if error_type == 'value_error.email':
                errors.append({
                    "field": "email",
                    "message": "Please enter a valid email address (e.g., user@example.com)"
                })
            elif error_type == 'string_too_short':
                errors.append({
                    "field": "email", 
                    "message": "Email address is too short. Please enter a valid email address."
                })
            elif error_type == 'string_too_long':
                errors.append({
                    "field": "email",
                    "message": "Email address is too long. Please enter a shorter email address."
                })
            else:
                errors.append({
                    "field": "email",
                    "message": "Please enter a valid email address."
                })
        
        elif field == 'username':
            if error_type == 'string_too_short':
                errors.append({
                    "field": "username",
                    "message": "Username must be at least 3 characters long."
                })
            elif error_type == 'string_too_long':
                errors.append({
                    "field": "username", 
                    "message": "Username must be less than 50 characters long."
                })
            elif 'regex' in error_msg.lower():
                errors.append({
                    "field": "username",
                    "message": "Username can only contain letters, numbers, underscores, and hyphens."
                })
            else:
                errors.append({
                    "field": "username",
                    "message": "Please enter a valid username."
                })
        
        elif field == 'password':
            if error_type == 'string_too_short':
                errors.append({
                    "field": "password",
                    "message": "Password must be at least 8 characters long."
                })
            elif error_type == 'string_too_long':
                errors.append({
                    "field": "password",
                    "message": "Password must be less than 128 characters long."
                })
            elif 'letter' in error_msg.lower():
                errors.append({
                    "field": "password",
                    "message": "Password must contain at least one letter."
                })
            elif 'number' in error_msg.lower() or 'digit' in error_msg.lower():
                errors.append({
                    "field": "password", 
                    "message": "Password must contain at least one number."
                })
            else:
                errors.append({
                    "field": "password",
                    "message": "Password must be at least 8 characters long and contain both letters and numbers."
                })
        
        elif field == 'role':
            errors.append({
                "field": "role",
                "message": "Please select a valid role (member or admin)."
            })
        
        else:
            # Generic error for unknown fields
            errors.append({
                "field": str(field),
                "message": "Please check your input and try again."
            })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Please check the following fields and try again:",
            "details": errors
        }
    )

# Custom exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions and return user-friendly messages.
    """
    # Handle structured error details
    if isinstance(exc.detail, dict):
        error_content = {
            "error": exc.detail.get("error", "Request Error"),
            "message": exc.detail.get("message", "An error occurred"),
            "field": exc.detail.get("field"),
            "success": False,
            "status_code": exc.status_code
        }
    else:
        error_content = {
            "error": "Request Error",
            "message": str(exc.detail),
            "success": False,
            "status_code": exc.status_code
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_content
    )

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend to communicate with the backend
# In production, replace "*" with your frontend URL for security
environment = os.getenv("ENVIRONMENT", "development")
allowed_origins = [
    "http://localhost:3000",  # For local development
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://teamapp-backend-python-1.onrender.com",  # Production backend
] if environment == "development" else [
    "https://your-frontend-domain.com",  # Replace with your actual frontend URL
    "http://localhost:3000",  # For local development
    "https://teamapp-backend-python-1.onrender.com",  # Production backend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["Access-Control-Allow-Origin"]
)

# Include routers
# Each router handles a specific set of endpoints
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)

# Root endpoint
@app.get("/")
def root():
    """
    Welcome endpoint to verify the API is running.
    
    Returns:
        Welcome message with available endpoints
    """
    return {
        "message": "Welcome to Kanban Board API",
        "endpoints": {
            "auth": "/auth - Authentication endpoints (signup, login)",
            "projects": "/projects - Project management endpoints",
            "tasks": "/tasks - Task management endpoints",
            "docs": "/docs - Interactive API documentation",
            "redoc": "/redoc - Alternative API documentation"
        }
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Status of the API
    """
    return {"status": "healthy", "service": "Kanban Board API"}

# Application startup event
@app.on_event("startup")
async def startup_event():
    """
    Run tasks on application startup.
    This is called when the server starts.
    """
    print(" Kanban Board API is starting up...")
    print(" Documentation available at: http://localhost:8000/docs")
    print(" Alternative docs at: http://localhost:8000/redoc")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Run tasks on application shutdown.
    This is called when the server stops.
    """
    print(" Kanban Board API is shutting down...")

# This block runs when the script is executed directly
# It's useful for development, but in production you'll use uvicorn command
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port, reload=True)
