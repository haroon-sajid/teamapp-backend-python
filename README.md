# Kanban Board Backend API

A RESTful API backend for a Kanban board application built with FastAPI, SQLAlchemy, and JWT authentication. This system provides complete project and task management capabilities with role-based access control.

## Features

- **JWT Authentication**: Secure user registration and login system
- **Role-Based Access Control**: Admin and Member user roles with different permissions
- **Project Management**: Complete CRUD operations for project management
- **Task Management**: Full task lifecycle management with assignment capabilities
- **RESTful API**: Clean, intuitive API endpoints following REST conventions
- **SQLite Database**: Lightweight, file-based database with no external dependencies
- **Auto-Generated Documentation**: Interactive API documentation with Swagger UI
- **Data Validation**: Comprehensive input validation using Pydantic schemas

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Python SQL toolkit and Object-Relational Mapping (ORM)
- **SQLite**: Embedded SQL database engine
- **JWT**: JSON Web Tokens for secure authentication
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for running the application

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/kanban-board-backend.git
cd kanban-board-backend
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/signup` - Register a new user account
- `POST /auth/login` - OAuth2 compatible login endpoint
- `POST /auth/login/json` - JSON-based login endpoint
- `GET /auth/me` - Get current authenticated user information

### Projects
- `GET /projects/` - Retrieve all projects (filtered by user role)
- `GET /projects/{project_id}` - Get specific project with associated tasks
- `POST /projects/` - Create a new project
- `PUT /projects/{project_id}` - Update an existing project
- `DELETE /projects/{project_id}` - Delete a project

### Tasks
- `GET /tasks/` - Retrieve tasks with optional filtering
- `GET /tasks/{task_id}` - Get specific task details
- `POST /tasks/` - Create a new task
- `PUT /tasks/{task_id}` - Update an existing task
- `DELETE /tasks/{task_id}` - Delete a task
- `POST /tasks/{task_id}/assign/{user_id}` - Assign task to a user
- `POST /tasks/{task_id}/unassign` - Remove task assignment

### System
- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint

## Usage Examples

### User Registration
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword",
    "role": "member"
  }'
```

### User Login
```bash
curl -X POST http://localhost:8000/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### Create Project (Authenticated)
```bash
curl -X POST http://localhost:8000/projects/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Project Name",
    "description": "Project description"
  }'
```

### Create Task (Authenticated)
```bash
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Task Title",
    "description": "Task description",
    "project_id": 1,
    "status": "todo"
  }'
```

## Database Schema

### Users
- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `hashed_password`: Encrypted password
- `role`: User role (admin/member)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### Projects
- `id`: Primary key
- `name`: Project name
- `description`: Project description
- `creator_id`: Foreign key to Users table
- `created_at`: Project creation timestamp
- `updated_at`: Last update timestamp

### Tasks
- `id`: Primary key
- `title`: Task title
- `description`: Task description
- `status`: Task status (todo/in_progress/done)
- `project_id`: Foreign key to Projects table
- `assignee_id`: Foreign key to Users table (optional)
- `created_at`: Task creation timestamp
- `updated_at`: Last update timestamp

## Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Role-Based Access**: Different permissions for admin and member users
- **Input Validation**: Comprehensive data validation and sanitization
- **CORS Configuration**: Configurable cross-origin resource sharing

## Project Structure

```
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration and session management
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic data validation schemas
├── requirements.txt     # Python package dependencies
├── routers/            # API route modules
│   ├── __init__.py
│   ├── auth.py         # Authentication endpoints
│   ├── projects.py     # Project management endpoints
│   └── tasks.py        # Task management endpoints
└── kanban_board.db     # SQLite database file (auto-generated)
```

## Configuration

### Environment Variables
For production deployment, configure these environment variables:
- `SECRET_KEY`: JWT signing secret key
- `DATABASE_URL`: Database connection string
- `CORS_ORIGINS`: Allowed CORS origins

### Security Considerations
- Change the default JWT secret key in production
- Configure CORS origins for your frontend domain
- Use environment variables for sensitive configuration
- Consider implementing rate limiting for production use

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Reset
To reset the database, delete the `kanban_board.db` file and restart the server.

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure you're running from the correct directory
   - Verify virtual environment is activated
   - Check all dependencies are installed

2. **Port Already in Use**
   - Use a different port: `uvicorn main:app --reload --port 8001`
   - Kill existing processes using the port

3. **Authentication Errors**
   - Verify token format: `Authorization: Bearer <token>`
   - Check token expiration (30 minutes default)
   - Ensure user exists and credentials are correct

4. **Database Errors**
   - Delete `kanban_board.db` to reset database
   - Check file permissions
   - Verify SQLite installation

## API Response Format

### Success Response
```json
{
  "id": 1,
  "name": "Example",
  "created_at": "2025-01-19T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
