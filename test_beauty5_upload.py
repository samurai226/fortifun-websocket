#!/usr/bin/env python3
"""
Simple test script to upload beauty5.jpg to S3 via Django backend
"""

import os
import requests
import sys

def upload_beauty5():
    print("🖼️  Uploading beauty5.jpg to S3 via Django backend")
    print("=" * 60)
    
    # Path to the beauty5.jpg file
    image_path = "../fortifun/assets/images/beauty5.jpg"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(image_path)
    print(f"📄 File: beauty5.jpg")
    print(f"📊 Size: {file_size:,} bytes")
    print(f"📁 Path: {os.path.abspath(image_path)}")
    print()
    
    # Django backend configuration
    django_url = "http://127.0.0.1:8000"
    upload_endpoint = f"{django_url}/api/v1/accounts/files/profile-picture"
    
    print(f"🌐 Django Server: {django_url}")
    print(f"📤 Upload Endpoint: {upload_endpoint}")
    print()
    
    # Test Django server
    print("🔍 Step 1: Checking Django server...")
    try:
        response = requests.get(django_url, timeout=5)
        print(f"✅ Django server is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server not accessible: {e}")
        return False
    print()
    
    # Upload the image
    print("📤 Step 2: Uploading beauty5.jpg...")
    
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'file': ('beauty5.jpg', image_file, 'image/jpeg')
            }
            
            print("   ⏳ Uploading to Django backend...")
            response = requests.post(
                upload_endpoint,
                files=files,
                timeout=60
            )
            
            print(f"   📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"   📄 Response: {result}")
                
                if 'url' in result:
                    s3_url = result['url']
                    print(f"   🔗 S3 URL: {s3_url}")
                    
                    # Verify S3 URL
                    print()
                    print("🔍 Step 3: Verifying S3 URL...")
                    try:
                        s3_response = requests.head(s3_url, timeout=10)
                        if s3_response.status_code == 200:
                            content_type = s3_response.headers.get('content-type', 'unknown')
                            content_length = s3_response.headers.get('content-length', 'unknown')
                            print("✅ S3 URL is accessible!")
                            print(f"   📋 Content-Type: {content_type}")
                            print(f"   📊 Content-Length: {content_length} bytes")
                            print(f"   🔗 You can view it at: {s3_url}")
                            return True
                        else:
                            print(f"❌ S3 URL returned status: {s3_response.status_code}")
                            return False
                    except Exception as e:
                        print(f"❌ Could not verify S3 URL: {e}")
                        return False
                else:
                    print("❌ No S3 URL in response")
                    return False
            else:
                print(f"❌ Upload failed with status: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
                
    except FileNotFoundError:
        print(f"❌ File not found: {image_path}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting beauty5.jpg Upload Test")
    print("=" * 60)
    
    success = upload_beauty5()
    
    if success:
        print()
        print("🎉 SUCCESS! beauty5.jpg uploaded to S3 successfully!")
        print("✅ Your Django backend is working with S3 integration")
    else:
        print()
        print("❌ FAILED! beauty5.jpg upload failed")
        print("💡 Check the Django server logs for more details")
    
    print("=" * 60)



















