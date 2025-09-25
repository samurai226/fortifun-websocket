#!/usr/bin/env python3
"""
Test script to upload a real photo to S3 via Django backend
This simulates what your Flutter app does when uploading a profile photo
"""

import os
import requests
import tempfile
from PIL import Image
import io

def create_test_image():
    """Create a simple test image"""
    # Create a simple colored image
    img = Image.new('RGB', (200, 200), color='lightblue')
    
    # Add some text to make it look like a profile photo
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 90), "TEST", fill='darkblue', font=font)
    draw.text((30, 120), "PHOTO", fill='darkblue', font=font)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes

def test_photo_upload():
    print("🧪 Testing Real Photo Upload to S3")
    print("=" * 50)
    
    # Create test image
    print("📸 Creating test profile photo...")
    test_image = create_test_image()
    
    # Django backend URL
    django_url = "http://localhost:8000"
    upload_endpoint = f"{django_url}/api/upload-profile-picture/"
    
    print(f"🌐 Django URL: {django_url}")
    print(f"📤 Upload endpoint: {upload_endpoint}")
    print()
    
    try:
        # Test if Django server is running
        print("🔍 Checking if Django server is running...")
        response = requests.get(django_url, timeout=5)
        print(f"✅ Django server is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server not accessible: {e}")
        print("💡 Make sure Django server is running on port 8000")
        return
    
    # Prepare the upload
    files = {
        'photo': ('test_profile_photo.jpg', test_image, 'image/jpeg')
    }
    
    data = {
        'user_id': 'test_user_123',
        'photo_type': 'profile_photo'
    }
    
    print("📤 Uploading photo to Django backend...")
    print(f"   File: test_profile_photo.jpg")
    print(f"   User ID: test_user_123")
    print(f"   Type: profile_photo")
    print()
    
    try:
        # Upload to Django
        response = requests.post(
            upload_endpoint,
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📄 Response: {result}")
            
            if 'url' in result:
                s3_url = result['url']
                print(f"🔗 S3 URL: {s3_url}")
                
                # Verify the URL is accessible
                print("🔍 Verifying S3 URL is accessible...")
                try:
                    s3_response = requests.head(s3_url, timeout=10)
                    if s3_response.status_code == 200:
                        print("✅ S3 URL is accessible!")
                        print(f"   Content-Type: {s3_response.headers.get('content-type', 'unknown')}")
                        print(f"   Content-Length: {s3_response.headers.get('content-length', 'unknown')} bytes")
                    else:
                        print(f"⚠️  S3 URL returned status: {s3_response.status_code}")
                except Exception as e:
                    print(f"⚠️  Could not verify S3 URL: {e}")
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_photo_upload()






























