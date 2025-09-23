# accounts/management/commands/assign_s3_images_to_users.py

import boto3
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Assign random images from S3 profil/ folder to existing users without profile pictures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be assigned without actually updating users'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of users to update',
            default=50
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        # Initialize S3 client
        if not (settings.AWS_ACCESS_KEY_ID and 
                settings.AWS_SECRET_ACCESS_KEY and 
                settings.AWS_STORAGE_BUCKET_NAME):
            self.stdout.write('❌ S3 credentials not configured')
            return

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Get list of images from S3 profil/ folder
        try:
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix='profil/'
            )
            
            if 'Contents' not in response:
                self.stdout.write('❌ No images found in S3 profil/ folder')
                return

            # Filter for image files
            image_keys = [
                obj['Key'] for obj in response['Contents'] 
                if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
            ]

            if not image_keys:
                self.stdout.write('❌ No image files found in S3 profil/ folder')
                return

            self.stdout.write(f'✅ Found {len(image_keys)} images in S3 profil/ folder')

        except Exception as e:
            self.stdout.write(f'❌ Error accessing S3: {e}')
            return

        # Get users without profile pictures
        users_without_pics = User.objects.filter(profile_picture__isnull=True)[:limit]
        users_with_empty_pics = User.objects.filter(profile_picture='')[:limit]
        
        all_users = list(users_without_pics) + list(users_with_empty_pics)
        # Remove duplicates
        all_users = list(set(all_users))

        if not all_users:
            self.stdout.write('✅ All users already have profile pictures!')
            return

        self.stdout.write(f'📋 Found {len(all_users)} users without profile pictures')

        # Assign random images
        updated_count = 0
        for user in all_users:
            if updated_count >= limit:
                break

            # Select random image
            selected_image_key = random.choice(image_keys)
            
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would assign {selected_image_key} to {user.username} ({user.email})')
            else:
                try:
                    # Update user's profile_picture field with S3 key
                    user.profile_picture = selected_image_key
                    user.save(update_fields=['profile_picture'])
                    self.stdout.write(f'✅ Assigned {selected_image_key} to {user.username}')
                except Exception as e:
                    self.stdout.write(f'❌ Error updating {user.username}: {e}')
                    continue

            updated_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'✅ Users updated: {updated_count}')
        self.stdout.write(f'📸 Images available: {len(image_keys)}')
        
        if dry_run:
            self.stdout.write('\n🔍 This was a DRY RUN - no users were actually updated')
            self.stdout.write('Run without --dry-run to assign the images')
        else:
            self.stdout.write('\n🎉 Image assignment completed!')

