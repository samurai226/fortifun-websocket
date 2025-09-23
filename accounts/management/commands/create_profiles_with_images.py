# accounts/management/commands/create_profiles_with_images.py

import os
import csv
import random
import boto3
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from matching.models import UserPreference, UserInterest, UserInterestRelation
from datetime import datetime, date
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create user profiles from CSV data with random images from profil folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            help='Path to CSV file with user data',
            default='users.csv'
        )
        parser.add_argument(
            '--s3-folder',
            type=str,
            help='S3 folder containing profile images (e.g., profil/)',
            default='profil/'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of profiles to create',
            default=50
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating profiles'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        s3_folder = options['s3_folder']
        limit = options['limit']
        dry_run = options['dry_run']

        # Check if CSV file exists
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        # Initialize S3 client
        if not (settings.AWS_ACCESS_KEY_ID and 
                settings.AWS_SECRET_ACCESS_KEY and 
                settings.AWS_STORAGE_BUCKET_NAME):
            raise CommandError('S3 credentials not configured')

        region_name = settings.AWS_S3_REGION_NAME or 'us-west-2'
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=region_name
        )

        # Get list of available images from S3
        try:
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix=s3_folder
            )
            
            if 'Contents' not in response:
                raise CommandError(f'No images found in S3 folder: {s3_folder}')

            # Filter for image files
            image_keys = [
                obj['Key'] for obj in response['Contents'] 
                if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
            ]

            if not image_keys:
                raise CommandError(f'No image files found in S3 folder: {s3_folder}')

            self.stdout.write(f'Found {len(image_keys)} images in S3 folder: {s3_folder}')

        except Exception as e:
            raise CommandError(f'Error accessing S3: {e}')

        self.stdout.write('✅ S3 client initialized - will assign existing S3 images')

        # Read CSV and create profiles
        created_count = 0
        skipped_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if created_count >= limit:
                    break

                try:
                    # Extract data from CSV
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    name = f"{first_name} {last_name}".strip()
                    bio = row.get('bio', '').strip()
                    location = row.get('location', '').strip()
                    gender = row.get('gender', '').strip()
                    age = row.get('age', '').strip()
                    interests = row.get('interests', '').strip()

                    if not name:
                        self.stdout.write(f'⚠️  Skipping row {created_count + 1}: missing name')
                        skipped_count += 1
                        continue

                    # Generate email from name
                    email_base = f"{first_name.lower()}.{last_name.lower()}"
                    email_domain = "example.com"
                    email = f"{email_base}@{email_domain}"

                    # Ensure email is unique
                    if User.objects.filter(email=email).exists():
                        suffix = 1
                        while True:
                            candidate = f"{email_base}{suffix}@{email_domain}"
                            if not User.objects.filter(email=candidate).exists():
                                email = candidate
                                break
                            suffix += 1

                    # Check if user already exists
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(f'⚠️  User with email {email} already exists, skipping')
                        skipped_count += 1
                        continue

                    # Randomly select an image from S3
                    selected_image_key = random.choice(image_keys)

                    if dry_run:
                        self.stdout.write(f'[DRY RUN] Would create user: {name} ({email}) with image: {selected_image_key}')
                        created_count += 1
                        continue

                    # Create username from email
                    username = email.split('@')[0]
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                    # Calculate date of birth from age
                    dob = None
                    if age:
                        try:
                            age_int = int(age)
                            current_year = datetime.now().year
                            birth_year = current_year - age_int
                            dob = date(birth_year, 1, 1)  # Use January 1st as default
                        except ValueError:
                            self.stdout.write(f'⚠️  Invalid age format for {name}: {age}')

                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='defaultpassword123',  # Default password
                        first_name=first_name,
                        last_name=last_name,
                        bio=bio,
                        location=location,
                        gender=gender.upper()[:1] if gender else '',
                        date_of_birth=dob
                    )

                    # Assign the existing S3 image to the user
                    try:
                        user.profile_picture = selected_image_key
                        user.save(update_fields=['profile_picture'])
                        self.stdout.write(f'✅ Assigned {selected_image_key} to {name}')
                    except Exception as e:
                        self.stdout.write(f'❌ Failed to assign image to {name}: {e}')

                    # Create user preferences
                    UserPreference.objects.get_or_create(user=user)

                    # Add interests
                    if interests:
                        interest_names = [i.strip() for i in interests.split(',') if i.strip()]
                        for interest_name in interest_names:
                            interest, created = UserInterest.objects.get_or_create(name=interest_name)
                            UserInterestRelation.objects.get_or_create(user=user, interest=interest)

                    created_count += 1
                    self.stdout.write(f'✅ Created profile {created_count}: {name} ({email})')

                except Exception as e:
                    self.stdout.write(f'❌ Error creating profile for row {created_count + 1}: {e}')
                    skipped_count += 1
                    continue

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'✅ Profiles created: {created_count}')
        self.stdout.write(f'⚠️  Profiles skipped: {skipped_count}')
        self.stdout.write(f'📸 Images available: {len(image_keys)}')
        
        if dry_run:
            self.stdout.write('\n🔍 This was a DRY RUN - no profiles were actually created')
            self.stdout.write('Run without --dry-run to create the profiles')
        else:
            self.stdout.write('\n🎉 Profile creation completed!')
