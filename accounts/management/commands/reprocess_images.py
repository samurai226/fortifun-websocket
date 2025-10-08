from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.image_processing import process_and_recode_image, validate_image_format, get_image_info
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reprocess all existing profile pictures to ensure Flutter compatibility'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Process only a specific user ID',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get users with profile pictures
        if options['user_id']:
            users = User.objects.filter(id=options['user_id'], profile_picture__isnull=False)
        else:
            users = User.objects.filter(profile_picture__isnull=False)
        
        total_users = users.count()
        self.stdout.write(f"Found {total_users} users with profile pictures")
        
        if options['dry_run']:
            self.stdout.write("DRY RUN - No images will be processed")
            for user in users:
                if user.profile_picture:
                    image_info = get_image_info(user.profile_picture)
                    self.stdout.write(f"User {user.id}: {user.profile_picture.name} - {image_info}")
            return
        
        processed_count = 0
        error_count = 0
        
        for user in users:
            try:
                if not user.profile_picture:
                    continue
                
                # Get original image info
                original_info = get_image_info(user.profile_picture)
                self.stdout.write(f"Processing user {user.id}: {user.profile_picture.name}")
                
                # Validate current image
                if not validate_image_format(user.profile_picture):
                    self.stdout.write(f"  ⚠️  Invalid format: {original_info}")
                    continue
                
                # Process and recode the image
                processed_file = process_and_recode_image(
                    user.profile_picture, 
                    max_size=(1024, 1024), 
                    quality=85
                )
                
                # Save the processed image
                user.profile_picture = processed_file
                user.save(update_fields=['profile_picture'])
                
                processed_count += 1
                self.stdout.write(f"  ✅ Processed successfully")
                
            except Exception as e:
                error_count += 1
                self.stdout.write(f"  ❌ Error processing user {user.id}: {e}")
                logger.error(f"Error processing user {user.id}: {e}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Reprocessing complete: {processed_count} processed, {error_count} errors"
            )
        )
