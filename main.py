"""
Main FastAPI application entry point.
This file sets up the FastAPI app and includes all routers.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend to communicate with the backend
# In production, replace "*" with your frontend URL for security
environment = os.getenv("ENVIRONMENT", "development")
allowed_origins = ["*"] if environment == "development" else [
    "https://your-frontend-domain.com",  # Replace with your actual frontend URL
    "http://localhost:3000",  # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
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
