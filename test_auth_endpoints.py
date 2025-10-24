#!/usr/bin/env python
"""
Simple test script to verify authentication endpoints
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

User = get_user_model()

def test_auth_endpoints():
    """Test the authentication endpoints"""
    client = Client()
    
    print("🧪 Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test 1: User Registration
    print("\n1. Testing User Registration...")
    register_data = {
        'name': 'Test User 2',
        'email': 'test2@example.com',
        'password': 'TestPass123!'
    }
    
    try:
        response = client.post('/api/v1/accounts/auth/register', 
                             data=json.dumps(register_data),
                             content_type='application/json')
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Registration successful")
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Access Token: {data.get('access', '')[:20]}...")
            return data
        else:
            print(f"   ❌ Registration failed: {response.content}")
            return None
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return None

def test_login():
    """Test user login"""
    client = Client()
    
    print("\n2. Testing User Login...")
    login_data = {
        'email': 'test2@example.com',
        'password': 'TestPass123!'
    }
    
    try:
        response = client.post('/api/v1/accounts/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful")
            print(f"   Access Token: {data.get('access', '')[:20]}...")
            return data
        else:
            print(f"   ❌ Login failed: {response.content}")
            return None
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_token_refresh():
    """Test token refresh"""
    client = Client()
    
    print("\n3. Testing Token Refresh...")
    
    # First login to get a refresh token
    login_data = {
        'email': 'test2@example.com',
        'password': 'TestPass123!'
    }
    
    try:
        login_response = client.post('/api/v1/accounts/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            refresh_token = login_data.get('refresh')
            
            if refresh_token:
                refresh_data = {'refresh': refresh_token}
                response = client.post('/api/v1/accounts/auth/refresh',
                                     data=json.dumps(refresh_data),
                                     content_type='application/json')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Token refresh successful")
                    print(f"   New Access Token: {data.get('access', '')[:20]}...")
                    return data
                else:
                    print(f"   ❌ Token refresh failed: {response.content}")
            else:
                print(f"   ❌ No refresh token received")
        else:
            print(f"   ❌ Login failed for refresh test")
    except Exception as e:
        print(f"   ❌ Token refresh error: {e}")
        return None

def test_logout():
    """Test logout endpoint"""
    client = Client()
    
    print("\n4. Testing Logout...")
    
    # First login to get a token
    login_data = {
        'email': 'test2@example.com',
        'password': 'TestPass123!'
    }
    
    try:
        login_response = client.post('/api/v1/accounts/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            access_token = login_data.get('access')
            
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                response = client.post('/api/v1/accounts/auth/logout',
                                      headers=headers,
                                      content_type='application/json')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ Logout successful")
                    return True
                else:
                    print(f"   ❌ Logout failed: {response.content}")
            else:
                print(f"   ❌ No access token received")
        else:
            print(f"   ❌ Login failed for logout test")
    except Exception as e:
        print(f"   ❌ Logout error: {e}")
        return None

def test_user_profile():
    """Test user profile endpoint"""
    client = Client()
    
    print("\n5. Testing User Profile...")
    
    # First login to get a token
    login_data = {
        'email': 'test2@example.com',
        'password': 'TestPass123!'
    }
    
    try:
        login_response = client.post('/api/v1/accounts/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            access_token = login_data.get('access')
            
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                response = client.get('/api/v1/accounts/users/me',
                                    headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Profile access successful")
                    print(f"   Username: {data.get('username')}")
                    print(f"   Email: {data.get('email')}")
                    return data
                else:
                    print(f"   ❌ Profile access failed: {response.content}")
            else:
                print(f"   ❌ No access token received")
        else:
            print(f"   ❌ Login failed for profile test")
    except Exception as e:
        print(f"   ❌ Profile access error: {e}")
        return None

if __name__ == '__main__':
    print("🚀 Starting Authentication Endpoint Tests")
    print("=" * 50)
    
    # Run tests
    test_auth_endpoints()
    test_login()
    test_token_refresh()
    test_logout()
    test_user_profile()
    
    print("\n" + "=" * 50)
    print("🏁 Authentication Endpoint Tests Complete")
