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

# Import models to ensure they are registered with SQLAlchemy
import models

# Import routers
from routers import auth, projects, tasks, users, teams

# Create database tables and ensure schema is current
try:
    from database_setup import create_tables
    create_tables()
except ImportError:
    Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title="Kanban Board API",
    description="A simple and beginner-friendly Kanban board backend built with FastAPI",
    version="1.0.0"
)

# ----------------------
# Custom Exception Handlers
# ----------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error.get('loc', ['unknown'])[-1]
        error_type = error.get('type', '')
        error_msg = error.get('msg', '')

        if field == 'email':
            if error_type == 'value_error.email':
                errors.append({"field": "email", "message": "Please enter a valid email address."})
            else:
                errors.append({"field": "email", "message": "Invalid email format."})

        elif field == 'username':
            errors.append({"field": "username", "message": "Invalid username format."})

        elif field == 'password':
            errors.append({"field": "password", "message": "Password must meet complexity requirements."})

        else:
            errors.append({"field": str(field), "message": "Invalid input."})

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": errors
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_content = {
        "error": "Request Error",
        "message": str(exc.detail),
        "success": False,
        "status_code": exc.status_code
    }
    return JSONResponse(status_code=exc.status_code, content=error_content)

# ----------------------
# CORS CONFIGURATION
# ----------------------
# Always allow localhost for development
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Add production frontend (Vercel)
vercel_origin = "https://teamapp-frontend-react.vercel.app"
preview_origin = "https://teamapp-frontend-react-4q6ea3ipa-haroons-projects-41fe01b2.vercel.app"

allowed_origins = default_origins + [vercel_origin, preview_origin]

# If you want dynamic control via ENV variable (optional)
cors_origin_env = os.getenv("CORS_ORIGIN")
if cors_origin_env:
    allowed_origins += cors_origin_env.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ----------------------
# Routers
# ----------------------
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(teams.router)

# ----------------------
# Health + Root
# ----------------------
@app.get("/")
def root():
    return {
        "message": "Welcome to Kanban Board API",
        "endpoints": {
            "auth": "/auth",
            "projects": "/projects",
            "tasks": "/tasks",
            "teams": "/teams",
            "users": "/users",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Kanban Board API"}

# ----------------------
# Lifecycle Events
# ----------------------
@app.on_event("startup")
async def startup_event():
    print(" Kanban Board API is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    print(" Kanban Board API is shutting down...")

# ----------------------
# Local Dev Server
# ----------------------
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port, reload=True)