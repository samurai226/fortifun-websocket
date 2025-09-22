# test_s3_upload.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
import os
import tempfile
from PIL import Image
import io

class Command(BaseCommand):
    help = 'Test S3 upload functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing S3 configuration...')
        
        # Check if S3 is configured
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_STORAGE_BUCKET_NAME):
            self.stdout.write(
                self.style.ERROR('S3 not configured. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME environment variables.')
            )
            return
        
        self.stdout.write(f'Bucket: {settings.AWS_STORAGE_BUCKET_NAME}')
        self.stdout.write(f'Region: {settings.AWS_S3_REGION_NAME}')
        self.stdout.write(f'Custom Domain: {settings.AWS_S3_CUSTOM_DOMAIN}')
        
        # Test S3 upload
        try:
            from storages.backends.s3boto3 import S3Boto3Storage
            
            # Create a test image
            img = Image.new('RGB', (100, 100), color='red')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            # Create test file
            test_file = ContentFile(img_io.getvalue(), name='test_profile_picture.jpg')
            
            # Upload to S3
            storage = S3Boto3Storage()
            filename = storage.save('test_uploads/test_profile_picture.jpg', test_file)
            url = storage.url(filename)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ S3 upload successful!')
            )
            self.stdout.write(f'Filename: {filename}')
            self.stdout.write(f'URL: {url}')
            
            # Clean up test file
            storage.delete(filename)
            self.stdout.write('Test file cleaned up.')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ S3 upload failed: {str(e)}')
            )
            self.stdout.write('Please check your AWS credentials and bucket permissions.')


















