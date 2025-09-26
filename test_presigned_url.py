#!/usr/bin/env python3
import boto3
import os

def test_presigned_url():
    """Test presigned URL generation"""
    try:
        # Test with a known file
        test_key = "profil/IMG-20250919-WA0165.jpg"
        
        s3 = boto3.client(
            's3',
            region_name='us-west-2',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            config=boto3.session.Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
            endpoint_url='https://s3.us-west-2.amazonaws.com'
        )
        
        # Generate presigned URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'fortu-app-assets-dev', 'Key': test_key},
            ExpiresIn=3600,
        )
        
        print(f"Generated presigned URL: {url}")
        
        # Test if the file exists
        try:
            response = s3.head_object(Bucket='fortu-app-assets-dev', Key=test_key)
            print(f"File exists: {test_key}")
            print(f"Content-Type: {response.get('ContentType', 'Unknown')}")
            print(f"Content-Length: {response.get('ContentLength', 'Unknown')}")
            print(f"Last-Modified: {response.get('LastModified', 'Unknown')}")
        except Exception as e:
            print(f"File does not exist or error accessing: {e}")
            
        # Test with a different file that we know exists
        try:
            test_key2 = "profil/IMG-20250919-WA0060.jpg"
            response = s3.head_object(Bucket='fortu-app-assets-dev', Key=test_key2)
            print(f"Alternative file exists: {test_key2}")
        except Exception as e:
            print(f"Alternative file error: {e}")
            
        # List some files in the profil folder
        try:
            response = s3.list_objects_v2(Bucket='fortu-app-assets-dev', Prefix='profil/', MaxKeys=5)
            if 'Contents' in response:
                print(f"Found {len(response['Contents'])} files in profil/ folder:")
                for obj in response['Contents']:
                    print(f"  - {obj['Key']} ({obj['Size']} bytes)")
            else:
                print("No files found in profil/ folder")
        except Exception as e:
            print(f"Error listing files: {e}")
            
    except Exception as e:
        print(f"Error generating presigned URL: {e}")

if __name__ == "__main__":
    test_presigned_url()
