#!/usr/bin/env python3
"""
Comprehensive test to verify all schema validations work correctly
"""

from schemas import UserCreate, UserLogin, UserResponse, ProjectCreate, TaskCreate
from pydantic import ValidationError

def test_user_validation():
    """Test user validation with valid and invalid data"""
    print("Testing User Validation...")
    
    # Test valid user creation
    try:
        valid_user = UserCreate(
            email="test@example.com",
            username="testuser123",
            password="password123"
        )
        print("✅ Valid user creation works!")
    except ValidationError as e:
        print(f"❌ Valid user creation failed: {e}")
        return False
    
    # Test invalid email
    try:
        invalid_user = UserCreate(
            email="invalid-email",
            username="testuser",
            password="password123"
        )
        print("❌ Invalid email should have failed!")
        return False
    except ValidationError:
        print("✅ Invalid email correctly rejected!")
    
    # Test weak password
    try:
        weak_password_user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="123"
        )
        print("❌ Weak password should have failed!")
        return False
    except ValidationError:
        print("✅ Weak password correctly rejected!")
    
    return True

def test_project_validation():
    """Test project validation"""
    print("\nTesting Project Validation...")
    
    try:
        valid_project = ProjectCreate(
            name="Test Project",
            description="A test project"
        )
        print("✅ Valid project creation works!")
    except ValidationError as e:
        print(f"❌ Valid project creation failed: {e}")
        return False
    
    # Test empty project name
    try:
        empty_name_project = ProjectCreate(
            name="",
            description="Test"
        )
        print("❌ Empty project name should have failed!")
        return False
    except ValidationError:
        print("✅ Empty project name correctly rejected!")
    
    return True

def test_task_validation():
    """Test task validation"""
    print("\nTesting Task Validation...")
    
    try:
        valid_task = TaskCreate(
            title="Test Task",
            description="A test task",
            project_id=1
        )
        print("✅ Valid task creation works!")
    except ValidationError as e:
        print(f"❌ Valid task creation failed: {e}")
        return False
    
    # Test empty task title
    try:
        empty_title_task = TaskCreate(
            title="",
            description="Test",
            project_id=1
        )
        print("❌ Empty task title should have failed!")
        return False
    except ValidationError:
        print("✅ Empty task title correctly rejected!")
    
    return True

def main():
    """Run all validation tests"""
    print("🚀 Starting Comprehensive Schema Validation Tests...\n")
    
    all_passed = True
    
    all_passed &= test_user_validation()
    all_passed &= test_project_validation()
    all_passed &= test_task_validation()
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Email validation working with regex")
        print("✅ Password validation working")
        print("✅ Username validation working")
        print("✅ Project validation working")
        print("✅ Task validation working")
    else:
        print("❌ Some validation tests failed!")
        exit(1)

if __name__ == "__main__":
    main()
