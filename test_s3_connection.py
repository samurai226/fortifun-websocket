#!/usr/bin/env python3
"""
Test script to check S3 connection and upload
"""

import os
import sys
import django
import boto3
from botocore.exceptions import ClientError

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
django.setup()

from django.conf import settings
from django.core.files.base import ContentFile

def test_s3_connection():
    print("🧪 Testing S3 connection and upload...")
    
    # Get AWS configuration from Django settings
    access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'fortu-app-assets-dev')
    region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-west-2')
    
    print(f"📦 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    print(f"🔑 Access Key: {'✅ Set' if access_key else '❌ Not set'}")
    print(f"🔐 Secret Key: {'✅ Set' if secret_key else '❌ Not set'}")
    
    if not access_key or not secret_key:
        print("❌ AWS credentials not configured")
        return False
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Test bucket access
        print("🔍 Testing bucket access...")
        response = s3_client.head_bucket(Bucket=bucket_name)
        print("✅ Bucket access successful")
        
        # Test file upload
        print("📤 Testing file upload...")
        test_content = b"Test file content for S3 upload"
        test_file = ContentFile(test_content)
        
        # Upload test file
        s3_key = 'test_uploads/test_file.txt'
        s3_client.upload_fileobj(
            test_file,
            bucket_name,
            s3_key
        )
        
        print(f"✅ File uploaded successfully to s3://{bucket_name}/{s3_key}")
        
        # Get file URL
        file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        print(f"🔗 File URL: {file_url}")
        
        # Test file download
        print("📥 Testing file download...")
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        downloaded_content = response['Body'].read()
        
        if downloaded_content == test_content:
            print("✅ File download successful and content matches")
        else:
            print("❌ File download failed - content mismatch")
            return False
        
        # Clean up test file
        print("🧹 Cleaning up test file...")
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        print("✅ Test file deleted")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ S3 Client Error: {error_code}")
        print(f"❌ Error Message: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_s3_connection()
