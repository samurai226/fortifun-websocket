#!/usr/bin/env python3
"""
Script to check what files are actually in the S3 bucket
"""

import os
import boto3
from botocore.exceptions import ClientError

def check_s3_bucket():
    print("🔍 Checking S3 Bucket Contents...")
    print("=" * 50)
    
    # Get environment variables
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    region = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ Missing AWS credentials")
        return
    
    print(f"📦 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    print()
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # List objects in bucket
        print("📋 Files in bucket:")
        print("-" * 30)
        
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            files = response['Contents']
            print(f"Found {len(files)} file(s):")
            print()
            
            for file in files:
                key = file['Key']
                size = file['Size']
                last_modified = file['LastModified']
                print(f"📄 {key}")
                print(f"   Size: {size} bytes")
                print(f"   Modified: {last_modified}")
                print(f"   URL: https://{bucket_name}.s3.{region}.amazonaws.com/{key}")
                print()
        else:
            print("📭 Bucket is empty - no files found")
            print()
            print("💡 This is normal if you haven't uploaded any photos yet!")
            print("   Try uploading a photo through your Flutter app to see files appear here.")
        
        # Check bucket policy and permissions
        print("🔐 Checking bucket permissions...")
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
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    check_s3_bucket()







































