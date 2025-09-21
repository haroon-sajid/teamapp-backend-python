#!/usr/bin/env python3
"""
Simple test to verify schemas work without email validation
"""

from schemas import UserCreate, UserLogin, UserResponse

# Test creating schemas
try:
    user_create = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )
    print("✅ UserCreate schema works!")
    
    user_login = UserLogin(
        email="test@example.com",
        password="testpass123"
    )
    print("✅ UserLogin schema works!")
    
    print("✅ All schemas working correctly!")
    
except Exception as e:
    print(f"❌ Schema error: {e}")
    exit(1)
