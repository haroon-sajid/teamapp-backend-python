# FastAPI Backend Deployment Guide for Render

This guide will help you deploy your FastAPI Kanban Board backend to Render.

## Prerequisites

1. A GitHub account
2. A Render account (sign up at [render.com](https://render.com))
3. Your code pushed to a GitHub repository

## Project Structure

Your project should have the following files:
```
teamapp-backend-python/
├── main.py                 # FastAPI application entry point
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── routers/               # API route modules
│   ├── auth.py
│   ├── projects.py
│   └── tasks.py
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── Procfile              # Process file for Render
├── render.yaml           # Render configuration
├── .gitignore            # Git ignore file
└── README.md
```

## Step-by-Step Deployment

### 1. Push Code to GitHub

First, make sure all your code is committed and pushed to GitHub:

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Prepare for Render deployment"

# Add your GitHub repository as remote
git remote add origin https://github.com/haroon-sajid/teamapp-backend-python.git

# Push to GitHub
git push -u origin main
```

### 2. Create a PostgreSQL Database on Render

1. Go to your Render dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Choose a name for your database (e.g., `kanban-board-db`)
4. Select the **Free** plan
5. Click **"Create Database"**
6. Wait for the database to be created
7. Copy the **External Database URL** (you'll need this later)

### 3. Deploy the Web Service

1. In your Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account if not already connected
3. Select your repository: `haroon-sajid/teamapp-backend-python`
4. Configure the service:
   - **Name**: `kanban-board-api` (or your preferred name)
   - **Environment**: **Docker**
   - **Region**: Choose the closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty (uses root)
   - **Dockerfile Path**: `./Dockerfile`

### 4. Set Environment Variables

In the **Environment** tab of your service, add these variables:

```
DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
HOST=0.0.0.0
PORT=8000
```

**Important Notes:**
- Use the PostgreSQL URL from step 2 for `DATABASE_URL`
- Generate a strong `SECRET_KEY` (you can use: `openssl rand -hex 32`)
- `HOST` and `PORT` are already set in the configuration

### 5. Deploy

1. Click **"Create Web Service"**
2. Render will start building your Docker image
3. The build process will:
   - Install Python dependencies
   - Copy your application files
   - Start the FastAPI server
4. Wait for the deployment to complete (usually 2-5 minutes)

### 6. Test Your Deployment

Once deployed, you can test your API:

1. **Health Check**: `https://your-service-name.onrender.com/health`
2. **API Documentation**: `https://your-service-name.onrender.com/docs`
3. **Alternative Docs**: `https://your-service-name.onrender.com/redoc`

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://user:pass@host:port/db` |
| `SECRET_KEY` | Secret key for JWT tokens | Yes | `your-secret-key-here` |
| `HOST` | Server host | No | `0.0.0.0` (default) |
| `PORT` | Server port | No | `8000` (default) |

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check that all dependencies are in `requirements.txt`
   - Ensure `Dockerfile` is in the root directory
   - Verify Python version compatibility

2. **Database Connection Error**
   - Verify `DATABASE_URL` is correct
   - Ensure PostgreSQL service is running
   - Check that `psycopg2-binary` is in requirements.txt

3. **Service Won't Start**
   - Check the logs in Render dashboard
   - Verify environment variables are set
   - Ensure the app binds to `0.0.0.0:8000`

4. **CORS Issues**
   - Update `allow_origins` in `main.py` with your frontend URL
   - Remove `["*"]` in production for security

### Checking Logs

1. Go to your service dashboard on Render
2. Click on the **"Logs"** tab
3. Look for error messages or startup information

## Local Development

To run locally with the same configuration:

1. Create a `.env` file:
```bash
DATABASE_URL=sqlite:///./kanban_board.db
SECRET_KEY=your-local-secret-key
HOST=0.0.0.0
PORT=8000
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Production Considerations

1. **Security**: Change the default `SECRET_KEY` to a strong, random value
2. **CORS**: Update `allow_origins` to only include your frontend domain
3. **Database**: Consider upgrading to a paid PostgreSQL plan for production
4. **Monitoring**: Set up logging and monitoring for production use
5. **Backups**: Regular database backups are recommended

## API Endpoints

Your deployed API will have these endpoints:

- `GET /` - Welcome message and API overview
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /tasks` - List tasks
- `POST /tasks` - Create task

## Support

If you encounter issues:

1. Check the Render logs first
2. Verify all environment variables are set correctly
3. Test locally to ensure the code works
4. Check the [Render documentation](https://render.com/docs)
5. Review the [FastAPI documentation](https://fastapi.tiangolo.com/)

Your FastAPI backend should now be successfully deployed on Render! 🚀

## Repository Information

- **GitHub Repository**: [https://github.com/haroon-sajid/teamapp-backend-python](https://github.com/haroon-sajid/teamapp-backend-python)
- **Author**: [@haroon-sajid](https://github.com/haroon-sajid)
- **Project Name**: Team App Backend Python
