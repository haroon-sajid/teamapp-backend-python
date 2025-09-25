#!/usr/bin/env python3
"""
Simple API test script to verify endpoints are working correctly.
This script tests the main endpoints that were causing 500 errors.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Change to production URL for testing production
TEST_EMAIL = "admin@teamapp.com"
TEST_PASSWORD = "admin123"

def test_api():
    """Test the main API endpoints."""
    
    print("🧪 Testing API endpoints...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False
    
    # Test 2: Login
    print("\n2. Testing login...")
    try:
        login_data = {
            "email_or_username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/auth/login-email", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Test 3: Get teams
    print("\n3. Testing teams endpoint...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/teams", headers=headers)
        if response.status_code == 200:
            teams = response.json()
            print(f"✅ Teams endpoint working - found {len(teams)} teams")
            if len(teams) > 0:
                team_id = teams[0]["id"]
                print(f"   Using team ID: {team_id}")
            else:
                print("   ⚠️ No teams found - this might cause issues")
                return False
        else:
            print(f"❌ Teams endpoint failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Teams endpoint error: {str(e)}")
        return False
    
    # Test 4: Create project
    print("\n4. Testing project creation...")
    try:
        project_data = {
            "name": "Test Project",
            "description": "Test project for API validation",
            "teamId": team_id
        }
        response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        if response.status_code == 200:
            project = response.json()
            project_id = project["id"]
            print(f"✅ Project creation successful - ID: {project_id}")
        else:
            print(f"❌ Project creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Project creation error: {str(e)}")
        return False
    
    # Test 5: Create task
    print("\n5. Testing task creation...")
    try:
        task_data = {
            "title": "Test Task",
            "description": "Test task for API validation",
            "status": "todo",
            "projectId": project_id
        }
        response = requests.post(f"{BASE_URL}/tasks/", json=task_data, headers=headers)
        if response.status_code == 200:
            task = response.json()
            task_id = task["id"]
            print(f"✅ Task creation successful - ID: {task_id}")
        else:
            print(f"❌ Task creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Task creation error: {str(e)}")
        return False
    
    # Test 6: Get tasks
    print("\n6. Testing tasks retrieval...")
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=headers)
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Tasks retrieval successful - found {len(tasks)} tasks")
        else:
            print(f"❌ Tasks retrieval failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Tasks retrieval error: {str(e)}")
        return False
    
    print("\n🎉 All API tests passed! The backend is working correctly.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        BASE_URL = "https://teamapp-backend-python-1.onrender.com"
        print("🌐 Testing production API...")
    else:
        print("🏠 Testing local API...")
    
    success = test_api()
    sys.exit(0 if success else 1)
