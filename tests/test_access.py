from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base
from models import User, UserRole, Team, TeamMember, TeamMemberRole, Project
from routers.auth import get_current_user
from database import get_db


# Set up an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_user_and_teams(db):
    user = User(email="test@example.com", username="testuser", hashed_password="x", role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)

    team_a = Team(name="Team A", description="A")
    team_b = Team(name="Team B", description="B")
    db.add_all([team_a, team_b])
    db.commit()
    db.refresh(team_a)
    db.refresh(team_b)

    # Add membership only to Team A
    tm = TeamMember(team_id=team_a.id, user_id=user.id, role=TeamMemberRole.MEMBER)
    db.add(tm)
    db.commit()

    return user, team_a, team_b


def test_create_project_for_inaccessible_team_returns_403():
    setup_db()
    app.dependency_overrides[get_db] = override_get_db

    db = next(override_get_db())
    try:
        user, team_a, team_b = create_user_and_teams(db)

        def override_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_current_user

        client = TestClient(app)
        # Attempt to create project under team_b where user is NOT a member
        resp = client.post("/projects/", json={
            "name": "My Board",
            "description": "Default project",
            "team_id": team_b.id
        })

        assert resp.status_code == 403, resp.text
        data = resp.json()
        assert "access" in (data.get("message", "").lower() or "access denied" in str(data)).lower()
    finally:
        db.close()


def test_create_project_for_accessible_team_returns_201():
    setup_db()
    app.dependency_overrides[get_db] = override_get_db

    db = next(override_get_db())
    try:
        user, team_a, _ = create_user_and_teams(db)

        def override_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_current_user

        client = TestClient(app)
        resp = client.post("/projects/", json={
            "name": "My Board",
            "description": "Default project",
            "team_id": team_a.id
        })
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data.get("team_id") == team_a.id
        assert data.get("name") == "My Board"
    finally:
        db.close()


def test_create_task_on_inaccessible_project_returns_403():
    setup_db()
    app.dependency_overrides[get_db] = override_get_db

    db = next(override_get_db())
    try:
        # user1 belongs only to team_a
        user1, team_a, team_b = create_user_and_teams(db)
        # create a project under team_b (inaccessible to user1)
        proj = Project(name="P2", description=None, creator_id=user1.id, team_id=team_b.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)

        def override_current_user():
            return user1

        app.dependency_overrides[get_current_user] = override_current_user
        client = TestClient(app)

        resp = client.post("/tasks/", json={
            "title": "Task 1",
            "description": "desc",
            "project_id": proj.id,
            "status": "todo"
        })

        assert resp.status_code == 403, resp.text
    finally:
        db.close()


def test_cors_preflight_projects_options_returns_allow_origin_header():
    setup_db()
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    resp = client.options(
        "/projects/",
        headers={
            "Origin": "https://teamapp-frontend-react.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    # Starlette's CORS should include the origin when allowed
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") in ("*", "https://teamapp-frontend-react.vercel.app")


