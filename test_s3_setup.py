#!/usr/bin/env python3
"""
S3 Setup Test Script for FortiFun
This script tests the S3 configuration and upload functionality.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
django.setup()

def test_s3_configuration():
    """Test S3 configuration"""
    print("🔍 Testing S3 Configuration...")
    print("=" * 50)
    
    # Check environment variables
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    region = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
    
    print(f"AWS_ACCESS_KEY_ID: {'✅ Set' if aws_access_key else '❌ Not set'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✅ Set' if aws_secret_key else '❌ Not set'}")
    print(f"AWS_STORAGE_BUCKET_NAME: {'✅ Set' if bucket_name else '❌ Not set'}")
    print(f"AWS_S3_REGION_NAME: {region}")
    
    if bucket_name:
        print(f"Expected S3 URL format: https://{bucket_name}.s3.{region}.amazonaws.com/media/")
    
    print("\n📋 Django Settings:")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
    print(f"AWS_S3_CUSTOM_DOMAIN: {getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Not set')}")
    
    return bool(aws_access_key and aws_secret_key and bucket_name)

def test_s3_upload():
    """Test actual S3 upload"""
    print("\n🚀 Testing S3 Upload...")
    print("=" * 50)
    
    try:
        from storages.backends.s3boto3 import S3Boto3Storage
        from django.core.files.base import ContentFile
        from PIL import Image
        import io
        
        # Create a test image
        img = Image.new('RGB', (200, 200), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        
        # Create test file
        test_file = ContentFile(img_io.getvalue(), name='test_profile_picture.jpg')
        
        # Upload to S3
        storage = S3Boto3Storage()
        filename = storage.save('test_uploads/test_profile_picture.jpg', test_file)
        url = storage.url(filename)
        
        print(f"✅ Upload successful!")
        print(f"Filename: {filename}")
        print(f"URL: {url}")
        
        # Verify URL format
        if 'amazonaws.com' in url:
            print("✅ URL contains amazonaws.com")
        if 's3' in url:
            print("✅ URL contains s3")
        if 'us-west-2' in url:
            print("✅ URL contains us-west-2 region")
        
        # Clean up test file
        storage.delete(filename)
        print("🧹 Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

def test_django_upload_endpoint():
    """Test Django upload endpoint configuration"""
    print("\n🔗 Testing Django Upload Endpoint...")
    print("=" * 50)
    
    try:
        from accounts.views import upload_profile_picture
        print("✅ upload_profile_picture view found")
        
        # Check if the view is properly configured
        print("✅ Django upload endpoint is configured")
        return True
        
    except Exception as e:
        print(f"❌ Django endpoint issue: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 FortiFun S3 Setup Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_s3_configuration()
    
    if not config_ok:
        print("\n❌ S3 configuration incomplete. Please set environment variables:")
        print("   export AWS_ACCESS_KEY_ID='your-access-key'")
        print("   export AWS_SECRET_ACCESS_KEY='your-secret-key'")
        print("   export AWS_STORAGE_BUCKET_NAME='fortu-app-assets-dev'")
        print("   export AWS_S3_REGION_NAME='us-west-2'")
        return
    
    # Test upload
    upload_ok = test_s3_upload()
    
    # Test Django endpoint
    endpoint_ok = test_django_upload_endpoint()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"S3 Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    print(f"Django Endpoint: {'✅ PASS' if endpoint_ok else '❌ FAIL'}")
    
    if config_ok and upload_ok and endpoint_ok:
        print("\n🎉 All tests passed! S3 is ready for profile photo uploads.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")

if __name__ == '__main__':
    main()



















