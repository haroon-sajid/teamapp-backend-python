"""
Main FastAPI application entry point.
This file sets up the FastAPI app and includes all routers.
"""
# change this line:

import os
from fastapi import FastAPI, Request, HTTPException, status
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
    for err in exc.errors():
        field = err.get("loc")[-1] if err.get("loc") else "unknown"
        error_type = err.get("type", "")
        message = err.get("msg", "Invalid input")

        # Customize common field messages
        if field == "email" and error_type == "value_error.email":
            message = "Please enter a valid email address."
        elif field == "password":
            message = "Password must include at least 8 characters with letters and numbers."
        elif field == "username":
            message = "Usernames should only include letters, numbers, or underscores."

        errors.append({"field": str(field), "message": message})

    first_message = errors[0]["message"] if errors else "Validation Error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": first_message,
            "details": errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
	"""
	If exc.detail is already a dict (our pattern from raise_http_error), return it
	directly so the client receives proper JSON. Otherwise fall back to a generic structure.
	"""
	detail = exc.detail

	# If the raised HTTPException already carries a structured dict, use it directly.
	if isinstance(detail, dict):
		# Copy to avoid mutation
		response = detail.copy()
		# Ensure consistent base fields
		response.setdefault("success", False)
		response.setdefault("status_code", exc.status_code)
		# If 'message' missing but 'error' present, promote error -> message
		if "message" not in response and "error" in response:
			response["message"] = response.get("error")
		return JSONResponse(status_code=exc.status_code, content=response)

	# Otherwise, return a normalized fallback JSON
	return JSONResponse(
		status_code=exc.status_code,
		content={
			"success": False,
			"error": "Request Error",
			"message": str(detail) if detail else "Something went wrong with your request.",
			"status_code": exc.status_code
		}
	)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
	"""
	Final fallback: log full traceback and return a consistent JSON error.
	"""
	import traceback
	print(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
	print(f"Request URL: {request.url}")
	print(f"Request Method: {request.method}")
	print(f"Traceback: {traceback.format_exc()}")

	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content={
			"success": False,
			"error": "Internal Server Error",
			"message": "Oops! Something went wrong on our end. Please try again later.",
			"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
		}
	)


# ----------------------
# CORS CONFIGURATION
# ----------------------
from fastapi.middleware.cors import CORSMiddleware
import os

# Define allowed origins for CORS
allowed_origins = [
    "https://teamapp-frontend-react.vercel.app",  # Production Vercel frontend
    "http://localhost:3000",                      # Local development
    "http://127.0.0.1:3000",                     # Local development alternative
]

# Add any additional origins from environment variable
cors_origin_env = os.getenv("CORS_ORIGIN")
if cors_origin_env:
    additional_origins = [origin.strip() for origin in cors_origin_env.split(',')]
    allowed_origins.extend(additional_origins)

print(f" CORS Configuration - Allowed Origins: {allowed_origins}")

# Add CORS middleware with comprehensive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight response for 1 hour
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

@app.get("/debug/db")
def debug_database():
    """Debug endpoint to check database connectivity and basic queries."""
    from database import SessionLocal
    from models import User, Team, Project
    
    db = SessionLocal()
    try:
        # Test basic queries
        user_count = db.query(User).count()
        team_count = db.query(Team).count()
        project_count = db.query(Project).count()
        
        return {
            "status": "database_connected",
            "user_count": user_count,
            "team_count": team_count,
            "project_count": project_count
        }
    except Exception as e:
        return {
            "status": "database_error",
            "error": str(e),
            "error_type": type(e).__name__
        }
    finally:
        db.close()

# ----------------------
# Lifecycle Events
# ----------------------
@app.on_event("startup")
async def startup_event():
    print(" Kanban Board API is starting up...")
    
    # Run database migration first
    try:
        from migrate_database import migrate_database
        migrate_database()
    except Exception as e:
        print(f" Warning: Could not migrate database: {str(e)}")
        print("The application will continue, but there may be schema issues.")
    
    # Initialize default team and admin user
    try:
        from init_default_team import create_default_team_and_admin
        create_default_team_and_admin()
    except Exception as e:
        print(f" Warning: Could not initialize default data: {str(e)}")
        print("The application will continue, but you may need to create teams manually.")

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