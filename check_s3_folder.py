#!/usr/bin/env python3
"""
Script to check the fortu-app-assets-dev folder in S3 bucket
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

def check_s3_folder():
    print("🔍 Checking fortu-app-assets-dev folder in S3 bucket...")
    print("=" * 60)
    
    # Get AWS configuration from Django settings
    access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'fortu-app-assets-dev')
    region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-west-2')
    
    print(f"📦 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    print(f"🔑 Access Key: {'✅ Set' if access_key else '❌ Not set'}")
    print(f"🔐 Secret Key: {'✅ Set' if secret_key else '❌ Not set'}")
    print()
    
    if not access_key or not secret_key:
        print("❌ AWS credentials not configured in Django settings")
        print("🔧 This means the app is running in development mode without S3")
        return
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print("🔍 Listing objects in fortu-app-assets-dev folder...")
        
        # List objects with prefix 'fortu-app-assets-dev/'
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='fortu-app-assets-dev/',
            MaxKeys=1000
        )
        
        if 'Contents' in response:
            objects = response['Contents']
            print(f"📁 Found {len(objects)} objects in fortu-app-assets-dev folder")
            print()
            
            # Group by folder structure
            folders = {}
            total_size = 0
            
            for obj in objects:
                key = obj['Key']
                size = obj['Size']
                last_modified = obj['LastModified']
                
                total_size += size
                
                # Extract folder structure
                parts = key.split('/')
                if len(parts) > 1:
                    folder = parts[1]  # First folder after fortu-app-assets-dev/
                    if folder not in folders:
                        folders[folder] = []
                    folders[folder].append({
                        'key': key,
                        'size': size,
                        'last_modified': last_modified
                    })
            
            # Display folder structure
            for folder, files in folders.items():
                print(f"📁 {folder}/ ({len(files)} files)")
                for file_info in files[:5]:  # Show first 5 files
                    size_mb = file_info['size'] / (1024 * 1024)
                    print(f"   📄 {file_info['key'].split('/')[-1]} ({size_mb:.2f} MB)")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
                print()
            
            # Summary
            total_size_mb = total_size / (1024 * 1024)
            print(f"📊 Total size: {total_size_mb:.2f} MB")
            print(f"📊 Total files: {len(objects)}")
            
            # Check for specific file types
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            image_count = 0
            image_size = 0
            
            for obj in objects:
                key = obj['Key'].lower()
                if any(key.endswith(ext) for ext in image_extensions):
                    image_count += 1
                    image_size += obj['Size']
            
            if image_count > 0:
                image_size_mb = image_size / (1024 * 1024)
                print(f"🖼️  Images: {image_count} files ({image_size_mb:.2f} MB)")
            
        else:
            print("❌ No objects found in fortu-app-assets-dev folder")
            print("🔍 This could mean:")
            print("   - The folder doesn't exist")
            print("   - No files have been uploaded yet")
            print("   - The prefix is incorrect")
        
        # Check if bucket exists and is accessible
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} is accessible")
        except ClientError as e:
            print(f"❌ Error accessing bucket {bucket_name}: {e}")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket {bucket_name} does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket {bucket_name}")
        elif error_code == 'InvalidAccessKeyId':
            print("❌ Invalid AWS access key")
        elif error_code == 'SignatureDoesNotMatch':
            print("❌ Invalid AWS secret key")
        else:
            print(f"❌ AWS Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_s3_folder()

