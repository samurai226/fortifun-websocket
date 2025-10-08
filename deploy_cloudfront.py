#!/usr/bin/env python3
"""
CloudFront CDN deployment script for FortiFun app
This script helps deploy and manage CloudFront distributions
"""

import os
import sys
import argparse
import boto3
from botocore.exceptions import ClientError
import time

def setup_aws_clients():
    """Setup AWS clients"""
    try:
        cloudfront = boto3.client('cloudfront')
        s3 = boto3.client('s3')
        return cloudfront, s3
    except Exception as e:
        print(f"❌ Error setting up AWS clients: {e}")
        print("Make sure AWS credentials are configured (aws configure)")
        sys.exit(1)

def create_s3_bucket(s3, bucket_name, region='us-west-2'):
    """Create S3 bucket if it doesn't exist"""
    try:
        # Check if bucket exists
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' already exists")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket doesn't exist, create it
            try:
                if region == 'us-east-1':
                    s3.create_bucket(Bucket=bucket_name)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                print(f"✅ Created S3 bucket '{bucket_name}' in region '{region}'")
                return True
            except ClientError as create_error:
                print(f"❌ Error creating S3 bucket: {create_error}")
                return False
        else:
            print(f"❌ Error checking S3 bucket: {e}")
            return False

def create_cloudfront_distribution(cloudfront, bucket_name, region='us-west-2'):
    """Create CloudFront distribution"""
    try:
        # Origin domain
        origin_domain = f"{bucket_name}.s3.{region}.amazonaws.com"
        
        # Distribution configuration
        distribution_config = {
            'CallerReference': f"fortifun-{int(time.time())}",
            'Comment': 'FortiFun CDN Distribution',
            'DefaultRootObject': 'index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [{
                    'Id': 'S3-Origin',
                    'DomainName': origin_domain,
                    'S3OriginConfig': {
                        'OriginAccessIdentity': ''
                    }
                }]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'S3-Origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,  # 24 hours
                'MaxTTL': 31536000,  # 1 year
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100',  # US, Canada, Europe
        }
        
        # Create distribution
        response = cloudfront.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution = response['Distribution']
        print(f"✅ Created CloudFront distribution:")
        print(f"   ID: {distribution['Id']}")
        print(f"   Domain: {distribution['DomainName']}")
        print(f"   Status: {distribution['Status']}")
        print(f"   Comment: {distribution['Comment']}")
        
        return distribution
        
    except ClientError as e:
        print(f"❌ Error creating CloudFront distribution: {e}")
        return None

def upload_static_files(s3, bucket_name, static_dir='static', media_dir='media'):
    """Upload static and media files to S3"""
    try:
        # Upload static files
        if os.path.exists(static_dir):
            print(f"📁 Uploading static files from {static_dir}...")
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = os.path.relpath(local_path, static_dir).replace('\\', '/')
                    s3_key = f"static/{s3_key}"
                    
                    s3.upload_file(
                        local_path,
                        bucket_name,
                        s3_key,
                        ExtraArgs={
                            'ContentType': get_content_type(file),
                            'CacheControl': 'max-age=31536000, public',  # 1 year
                            'ACL': 'public-read'
                        }
                    )
                    print(f"   ✅ Uploaded: {s3_key}")
        
        # Upload media files
        if os.path.exists(media_dir):
            print(f"📁 Uploading media files from {media_dir}...")
            for root, dirs, files in os.walk(media_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = os.path.relpath(local_path, media_dir).replace('\\', '/')
                    s3_key = f"media/{s3_key}"
                    
                    s3.upload_file(
                        local_path,
                        bucket_name,
                        s3_key,
                        ExtraArgs={
                            'ContentType': get_content_type(file),
                            'CacheControl': 'max-age=86400, public',  # 24 hours
                            'ACL': 'public-read'
                        }
                    )
                    print(f"   ✅ Uploaded: {s3_key}")
        
        print("✅ File upload completed")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading files: {e}")
        return False

def get_content_type(filename):
    """Get content type from filename"""
    ext = os.path.splitext(filename)[1].lower()
    
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
    }
    
    return content_types.get(ext, 'application/octet-stream')

def wait_for_deployment(cloudfront, distribution_id, timeout=1800):
    """Wait for CloudFront distribution to be deployed"""
    print(f"⏳ Waiting for CloudFront distribution {distribution_id} to be deployed...")
    print("   This may take 15-20 minutes...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = cloudfront.get_distribution(Id=distribution_id)
            status = response['Distribution']['Status']
            
            if status == 'Deployed':
                print("✅ CloudFront distribution is deployed and ready!")
                return True
            else:
                print(f"   Status: {status} (waiting...)")
                time.sleep(30)  # Check every 30 seconds
                
        except ClientError as e:
            print(f"❌ Error checking deployment status: {e}")
            return False
    
    print("⏰ Timeout waiting for deployment")
    return False

def create_invalidation(cloudfront, distribution_id, paths=None):
    """Create CloudFront cache invalidation"""
    if paths is None:
        paths = ['/*']
    
    try:
        response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f"invalidation-{int(time.time())}"
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        print(f"✅ Created cache invalidation: {invalidation_id}")
        print(f"   Paths: {', '.join(paths)}")
        return invalidation_id
        
    except ClientError as e:
        print(f"❌ Error creating invalidation: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Deploy CloudFront CDN for FortiFun app')
    parser.add_argument('--bucket-name', default='fortu-app-assets-dev', help='S3 bucket name')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    parser.add_argument('--static-dir', default='static', help='Static files directory')
    parser.add_argument('--media-dir', default='media', help='Media files directory')
    parser.add_argument('--create-bucket', action='store_true', help='Create S3 bucket')
    parser.add_argument('--upload-files', action='store_true', help='Upload static/media files')
    parser.add_argument('--create-distribution', action='store_true', help='Create CloudFront distribution')
    parser.add_argument('--invalidate-cache', action='store_true', help='Invalidate CloudFront cache')
    parser.add_argument('--distribution-id', help='CloudFront distribution ID for invalidation')
    parser.add_argument('--paths', nargs='+', default=['/*'], help='Paths to invalidate')
    
    args = parser.parse_args()
    
    print("🚀 FortiFun CloudFront CDN Deployment")
    print("=" * 50)
    
    # Setup AWS clients
    cloudfront, s3 = setup_aws_clients()
    
    # Create S3 bucket if requested
    if args.create_bucket:
        if not create_s3_bucket(s3, args.bucket_name, args.region):
            sys.exit(1)
    
    # Upload files if requested
    if args.upload_files:
        if not upload_static_files(s3, args.bucket_name, args.static_dir, args.media_dir):
            sys.exit(1)
    
    # Create CloudFront distribution if requested
    distribution_id = None
    if args.create_distribution:
        distribution = create_cloudfront_distribution(cloudfront, args.bucket_name, args.region)
        if distribution:
            distribution_id = distribution['Id']
            
            # Wait for deployment
            if not wait_for_deployment(cloudfront, distribution_id):
                print("⚠️  Deployment may still be in progress")
        else:
            sys.exit(1)
    
    # Invalidate cache if requested
    if args.invalidate_cache:
        target_distribution_id = args.distribution_id or distribution_id
        if not target_distribution_id:
            print("❌ Distribution ID required for cache invalidation")
            sys.exit(1)
        
        create_invalidation(cloudfront, target_distribution_id, args.paths)
    
    print("\n✅ CloudFront CDN deployment completed!")
    print("\nNext steps:")
    print("1. Update your Django settings with the CloudFront domain")
    print("2. Update your Flutter app with the CloudFront domain")
    print("3. Test the CDN by accessing your static/media files")

if __name__ == '__main__':
    main()


