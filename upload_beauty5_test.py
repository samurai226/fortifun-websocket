#!/usr/bin/env python3
"""
Test script to upload beauty5.jpg from Flutter assets to S3 via Django backend
"""

import os
import requests
import time

def upload_beauty5_image():
    print("🖼️  Uploading beauty5.jpg to S3")
    print("=" * 50)
    
    # Path to the beauty5.jpg file
    image_path = "../fortifun/assets/images/beauty5.jpg"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(image_path)
    print(f"📄 File: beauty5.jpg")
    print(f"📊 Size: {file_size:,} bytes")
    print(f"📁 Path: {image_path}")
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
    
    # Test 2: Upload the beauty5.jpg image
    print("📤 Step 2: Uploading beauty5.jpg...")
    
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'file': ('beauty5.jpg', image_file, 'image/jpeg')
            }
            
            print("   ⏳ Uploading to Django backend...")
            start_time = time.time()
            
            response = requests.post(
                upload_endpoint,
                files=files,
                timeout=60  # Longer timeout for larger images
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
                                print(f"✅ Image is accessible!")
                                print(f"   📊 Downloaded size: {len(img_response.content):,} bytes")
                                print(f"   🔗 You can view it at: {s3_url}")
                            else:
                                print(f"⚠️  Could not download image: {img_response.status_code}")
                            
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
    print("🚀 Starting beauty5.jpg Upload Test")
    print("=" * 50)
    
    success = upload_beauty5_image()
    
    if success:
        check_s3_bucket_after_upload()
        print()
        print("🎉 SUCCESS! beauty5.jpg uploaded to S3 successfully!")
        print("✅ Your Flutter app can now upload real images to S3")
    else:
        print()
        print("❌ FAILED! beauty5.jpg upload failed")
        print("💡 Check the Django server logs for more details")
    
    print("=" * 50)






































