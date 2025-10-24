#!/usr/bin/env python3
"""
Script to check S3 bucket contents using Django settings
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

def check_s3_bucket():
    print("🔍 Checking S3 Bucket Contents using Django settings...")
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
        print("💡 This means the app is running in development mode without S3")
        print("   Check the local media folder for uploaded files instead.")
        return
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # List objects in bucket
        print("📋 Files in S3 bucket:")
        print("-" * 40)
        
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            files = response['Contents']
            print(f"Found {len(files)} file(s) in S3:")
            print()
            
            # Count by file type
            image_count = 0
            profile_count = 0
            other_count = 0
            
            for file in files:
                key = file['Key']
                size = file['Size']
                last_modified = file['LastModified']
                
                # Categorize files
                if key.startswith('profil/') or key.startswith('profile/'):
                    profile_count += 1
                elif key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    image_count += 1
                else:
                    other_count += 1
                
                print(f"📄 {key}")
                print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
                print(f"   Modified: {last_modified}")
                print(f"   URL: https://{bucket_name}.s3.{region}.amazonaws.com/{key}")
                print()
            
            print("📊 Summary:")
            print(f"   🖼️  Profile Images: {profile_count}")
            print(f"   🎨 Other Images: {image_count}")
            print(f"   📁 Other Files: {other_count}")
            print(f"   📦 Total Files: {len(files)}")
            
        else:
            print("📭 S3 bucket is empty - no files found")
            print()
            print("💡 This is normal if you haven't uploaded any photos yet!")
            print("   Try uploading a photo through your Flutter app to see files appear here.")
        
        # Check bucket policy and permissions
        print("\n🔐 Checking bucket permissions...")
        try:
            bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)
            print("✅ Bucket has a policy configured")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print("ℹ️  No bucket policy (this is normal)")
            else:
                print(f"⚠️  Could not check bucket policy: {e}")
        
        # Check if bucket allows public read
        try:
            bucket_acl = s3_client.get_bucket_acl(Bucket=bucket_name)
            print("✅ Bucket ACL accessible")
        except ClientError as e:
            print(f"⚠️  Could not check bucket ACL: {e}")
            
    except ClientError as e:
        print(f"❌ Error accessing S3: {e}")
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"   The bucket '{bucket_name}' does not exist")
        elif e.response['Error']['Code'] == 'AccessDenied':
            print("   Access denied - check your AWS credentials")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    check_s3_bucket()

