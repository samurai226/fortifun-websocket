import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reprocess all existing images to fix EncodingError issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of images to process',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        try:
            # List all images in the profil/ folder
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='profil/'
            )
            
            images = []
            for obj in response.get('Contents', []):
                if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    images.append(obj['Key'])
            
            if not images:
                self.stdout.write(self.style.WARNING('No images found in profil/ folder'))
                return
            
            if limit:
                images = images[:limit]
            
            self.stdout.write(f'Found {len(images)} images to process')
            
            processed_count = 0
            error_count = 0
            
            for i, image_key in enumerate(images, 1):
                try:
                    self.stdout.write(f'Processing {i}/{len(images)}: {image_key}')
                    
                    if dry_run:
                        self.stdout.write(f'  [DRY RUN] Would process: {image_key}')
                        continue
                    
                    # Download the image
                    response = s3_client.get_object(Bucket=bucket_name, Key=image_key)
                    image_data = response['Body'].read()
                    
                    # Process the image
                    processed_data = self._process_image(image_data)
                    
                    if processed_data:
                        # Upload the processed image back to S3
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=image_key,
                            Body=processed_data,
                            ContentType='image/jpeg'
                        )
                        
                        processed_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Processed: {image_key}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ❌ Failed to process: {image_key}'))
                        error_count += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error processing {image_key}: {str(e)}'))
                    error_count += 1
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reprocessing complete: {processed_count} processed, {error_count} errors'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Dry run complete: Would process {len(images)} images'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def _process_image(self, image_data):
        """Process image data to ensure Flutter compatibility"""
        try:
            # Open image from bytes
            with Image.open(BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (1024, 1024)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save as JPEG with high quality
                output = BytesIO()
                img.save(output, format='JPEG', quality=95, optimize=True)
                output.seek(0)
                
                return output.getvalue()
                
        except Exception as e:
            logger.error(f'Error processing image: {str(e)}')
            return None