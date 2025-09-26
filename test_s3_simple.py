#!/usr/bin/env python3
import boto3
import os

def test_s3_access():
    """Test S3 access and presigned URL generation"""
    try:
        s3 = boto3.client(
            's3',
            region_name='us-west-2',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            config=boto3.session.Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
            endpoint_url='https://s3.us-west-2.amazonaws.com'
        )
        
        print("S3 client created successfully")
        
        # List files in profil folder
        print("Listing files in profil/ folder...")
        response = s3.list_objects_v2(Bucket='fortu-app-assets-dev', Prefix='profil/', MaxKeys=3)
        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} files:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                
                # Test presigned URL for first file
                if obj == response['Contents'][0]:
                    print(f"Generating presigned URL for: {obj['Key']}")
                    url = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': 'fortu-app-assets-dev', 'Key': obj['Key']},
                        ExpiresIn=3600,
                    )
                    print(f"Presigned URL: {url}")
        else:
            print("No files found in profil/ folder")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_s3_access()
