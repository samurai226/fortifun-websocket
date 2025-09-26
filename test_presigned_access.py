#!/usr/bin/env python3
import boto3
import os
import requests

def test_presigned_url_access():
    """Test if presigned URLs work for actual image files"""
    try:
        s3 = boto3.client(
            's3',
            region_name='us-west-2',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            config=boto3.session.Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
            endpoint_url='https://s3.us-west-2.amazonaws.com'
        )
        
        # Test with an actual image file
        test_key = "profil/IMG-20250919-WA0043.jpg"
        
        # Generate presigned URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'fortu-app-assets-dev', 'Key': test_key},
            ExpiresIn=3600,
        )
        
        print(f"Generated presigned URL: {url}")
        
        # Test the URL with requests
        try:
            response = requests.head(url, timeout=10)
            print(f"HTTP Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
            
            if response.status_code == 200:
                print("✅ Presigned URL works!")
            else:
                print(f"❌ Presigned URL failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing presigned URL: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_presigned_url_access()
