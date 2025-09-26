#!/usr/bin/env python3
import boto3
import os

# Test S3 presigned URL generation
s3 = boto3.client(
    's3',
    region_name='us-west-2',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    config=boto3.session.Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    endpoint_url='https://s3.us-west-2.amazonaws.com'
)

# Generate presigned URL for a known file
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'fortu-app-assets-dev', 'Key': 'profil/IMG-20250919-WA0043.jpg'},
    ExpiresIn=3600,
)

print("Presigned URL generated successfully!")
print(f"URL: {url}")

# Test with curl equivalent
import subprocess
import sys

try:
    result = subprocess.run([
        'curl', '-I', url
    ], capture_output=True, text=True, timeout=10)
    
    print(f"Curl exit code: {result.returncode}")
    print(f"Curl stdout: {result.stdout}")
    print(f"Curl stderr: {result.stderr}")
    
except Exception as e:
    print(f"Curl test failed: {e}")
