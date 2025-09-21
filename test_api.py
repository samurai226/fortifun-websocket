#!/usr/bin/env python3
"""
Test script for FortiApp Django API
Tests all major endpoints to ensure they're working correctly
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def test_api_health():
    """Test if the API is accessible"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ API is accessible - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not accessible: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    print("\n🔍 Testing User Registration...")
    
    # Test data
    user_data = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/accounts/auth/register", 
                               json=user_data, 
                               headers=HEADERS)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ User registration successful")
            return response.json()
        else:
            print("❌ User registration failed")
            return None
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_user_login(email, password):
    """Test user login endpoint"""
    print("\n🔍 Testing User Login...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/accounts/auth/login", 
                               json=login_data, 
                               headers=HEADERS)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ User login successful")
            return response.json()
        else:
            print("❌ User login failed")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_user_profile(token):
    """Test user profile endpoint"""
    print("\n🔍 Testing User Profile...")
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/accounts/users/me", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ User profile retrieved successfully")
            return response.json()
        else:
            print("❌ User profile retrieval failed")
            return None
            
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return None

def test_matching_endpoints(token):
    """Test matching related endpoints"""
    print("\n🔍 Testing Matching Endpoints...")
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    # Test potential matches
    try:
        response = requests.get(f"{BASE_URL}/matching/potential-matches/", headers=headers)
        print(f"Potential Matches - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Potential matches endpoint working")
        else:
            print("❌ Potential matches endpoint failed")
    except Exception as e:
        print(f"❌ Potential matches error: {e}")
    
    # Test matches
    try:
        response = requests.get(f"{BASE_URL}/matching/matches/", headers=headers)
        print(f"Matches - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Matches endpoint working")
        else:
            print("❌ Matches endpoint failed")
    except Exception as e:
        print(f"❌ Matches error: {e}")

def test_conversation_endpoints(token):
    """Test conversation endpoints"""
    print("\n🔍 Testing Conversation Endpoints...")
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    # Test conversations list
    try:
        response = requests.get(f"{BASE_URL}/conversations/", headers=headers)
        print(f"Conversations - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Conversations endpoint working")
        else:
            print("❌ Conversations endpoint failed")
    except Exception as e:
        print(f"❌ Conversations error: {e}")

def main():
    """Main test function"""
    print("🚀 Starting FortiApp API Tests")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("\n❌ API is not accessible. Please start the Django server first.")
        print("Run: python manage.py runserver")
        return
    
    # Test user registration
    user_data = test_user_registration()
    if not user_data:
        print("\n❌ Cannot proceed without user registration")
        return
    
    # Test user login
    login_data = test_user_login(user_data.get('email', 'test@example.com'), 'testpassword123')
    if not login_data:
        print("\n❌ Cannot proceed without user login")
        return
    
    token = login_data.get('access')
    if not token:
        print("\n❌ No access token received")
        return
    
    # Test authenticated endpoints
    test_user_profile(token)
    test_matching_endpoints(token)
    test_conversation_endpoints(token)
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")

if __name__ == "__main__":
    main()

