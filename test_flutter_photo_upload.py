#!/usr/bin/env python3
"""
Test script to simulate Flutter app photo upload to S3
This tests the exact same flow your Flutter app uses
"""

import os
import requests
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io
import time

def create_realistic_profile_photo():
    """Create a realistic test profile photo"""
    # Create a 400x400 profile photo
    img = Image.new('RGB', (400, 400), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Add a circular background
    draw.ellipse([50, 50, 350, 350], fill='#4CAF50', outline='#2E7D32', width=4)
    
    # Add initials
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    draw.text((150, 150), "FP", fill='white', font=font)
    
    # Add some details
    try:
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        small_font = ImageFont.load_default()
    
    draw.text((120, 280), "FortiFun", fill='white', font=small_font)
    draw.text((140, 310), "Profile", fill='white', font=small_font)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    
    return img_bytes

def test_flutter_photo_upload():
    print("🧪 Testing Flutter Photo Upload to S3")
    print("=" * 60)
    
    # Create realistic test photo
    print("📸 Creating realistic profile photo...")
    test_photo = create_realistic_profile_photo()
    photo_size = len(test_photo.getvalue())
    print(f"   Photo size: {photo_size:,} bytes")
    print()
    
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
        print("💡 Make sure Django server is running on port 8000")
        return False
    print()
    
    # Test 2: Upload photo (simulating Flutter app)
    print("📤 Step 2: Uploading photo (Flutter simulation)...")
    
    # Prepare the upload exactly like Flutter would
    files = {
        'file': ('profile_photo.jpg', test_photo, 'image/jpeg')
    }
    
    # Don't set Content-Type header - let requests handle it for multipart
    headers = {}
    
    print(f"   📄 File: profile_photo.jpg")
    print(f"   👤 User ID: test_user_123")
    print(f"   📋 Type: profile_photo")
    print(f"   📊 Size: {photo_size:,} bytes")
    print()
    
    try:
        # Upload to Django (this should save to S3)
        print("   ⏳ Uploading to Django backend...")
        start_time = time.time()
        
        response = requests.post(
            upload_endpoint,
            files=files,
            headers=headers,
            timeout=30
        )
        
        upload_time = time.time() - start_time
        print(f"   ⏱️  Upload time: {upload_time:.2f} seconds")
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"   📄 Response: {result}")
            
            if 'url' in result:
                s3_url = result['url']
                print(f"   🔗 S3 URL: {s3_url}")
                
                # Test 3: Verify S3 URL is accessible
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
                        
                        # Test 4: Check if it's actually a valid image
                        print()
                        print("🖼️  Step 4: Verifying image content...")
                        img_response = requests.get(s3_url, timeout=10)
                        if img_response.status_code == 200:
                            try:
                                img = Image.open(io.BytesIO(img_response.content))
                                print(f"✅ Image is valid!")
                                print(f"   📐 Dimensions: {img.size[0]}x{img.size[1]}")
                                print(f"   🎨 Format: {img.format}")
                                print(f"   🎯 Mode: {img.mode}")
                            except Exception as e:
                                print(f"⚠️  Image verification failed: {e}")
                        
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
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_s3_bucket_after_upload():
    """Check what's in the S3 bucket after upload"""
    print()
    print("🔍 Step 5: Checking S3 bucket contents...")
    print("-" * 40)
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Get environment variables
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
        region = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
        
        if not all([access_key, secret_key, bucket_name]):
            print("❌ Missing AWS credentials")
            return
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # List objects in bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            files = response['Contents']
            print(f"📦 Found {len(files)} file(s) in bucket:")
            print()
            
            for file in files:
                key = file['Key']
                size = file['Size']
                last_modified = file['LastModified']
                print(f"📄 {key}")
                print(f"   Size: {size:,} bytes")
                print(f"   Modified: {last_modified}")
                print(f"   URL: https://{bucket_name}.s3.{region}.amazonaws.com/{key}")
                print()
        else:
            print("📭 No files found in bucket")
            
    except Exception as e:
        print(f"⚠️  Could not check S3 bucket: {e}")

if __name__ == "__main__":
    print("🚀 Starting Flutter Photo Upload Test")
    print("=" * 60)
    
    success = test_flutter_photo_upload()
    
    if success:
        check_s3_bucket_after_upload()
        print()
        print("🎉 SUCCESS! Photo upload test completed successfully!")
        print("✅ Your Flutter app should now be able to upload photos to S3")
    else:
        print()
        print("❌ FAILED! Photo upload test failed")
        print("💡 Check the Django server logs for more details")
    
    print("=" * 60)
