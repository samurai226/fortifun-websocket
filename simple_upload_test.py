#!/usr/bin/env python3
"""
Simple test to check if the upload endpoint works
"""

import requests
import tempfile
import os

def test_simple_upload():
    print("🧪 Simple Upload Test")
    print("=" * 40)
    
    # Create a simple test file
    test_content = b"This is a test file for upload"
    
    # Django backend configuration
    django_url = "http://127.0.0.1:8000"
    upload_endpoint = f"{django_url}/api/v1/accounts/files/profile-picture"
    
    print(f"🌐 Django Server: {django_url}")
    print(f"📤 Upload Endpoint: {upload_endpoint}")
    print()
    
    # Test 1: Check if Django server is running
    print("🔍 Step 1: Checking Django server...")
    try:
        response = requests.get(django_url, timeout=5)
        print(f"✅ Django server is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server not accessible: {e}")
        return False
    print()
    
    # Test 2: Try upload with simple file
    print("📤 Step 2: Testing upload...")
    
    files = {
        'file': ('test.txt', test_content, 'text/plain')
    }
    
    try:
        response = requests.post(
            upload_endpoint,
            files=files,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
            return True
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_simple_upload()








