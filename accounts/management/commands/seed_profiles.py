from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

import csv
import json
import os
import io
import requests
from PIL import Image


class Command(BaseCommand):
    help = (
        'Seed users with profile photos. Supports CSV or JSON input and either local images '
        'folder or remote image URLs. When S3 is configured in settings, images are uploaded to S3.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to CSV or JSON file with user data')
        parser.add_argument('--images-dir', type=str, help='Directory containing profile images (optional if using URLs)')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of users to import (0 = no limit)')
        parser.add_argument('--default-password', type=str, default='Password123!', help='Default password for created users')

    def handle(self, *args, **options):
        data_path = options['file']
        images_dir = options.get('images_dir')
        limit = options.get('limit') or 0
        default_password = options['default_password']

        if not os.path.exists(data_path):
            raise CommandError(f'Input file not found: {data_path}')

        ext = os.path.splitext(data_path)[1].lower()
        if ext not in ('.csv', '.json'):
            raise CommandError('Input file must be .csv or .json')

        records = self._load_records(data_path, ext)
        if limit > 0:
            records = records[:limit]

        User = get_user_model()
        created, updated = 0, 0

        # Log storage backend
        storage_backend = getattr(settings, 'DEFAULT_FILE_STORAGE', 'local')
        self.stdout.write(self.style.NOTICE(f'Using storage backend: {storage_backend}'))

        for idx, rec in enumerate(records, start=1):
            try:
                username = rec.get('username') or self._derive_username(rec)
                email = rec.get('email') or f'{username}@example.com'
                first_name = rec.get('first_name', '')
                last_name = rec.get('last_name', '')
                gender = rec.get('gender', '')
                bio = rec.get('bio', '')
                location = rec.get('location', '')

                # Optional fields not mandatory in model
                phone_number = rec.get('phone_number', '')
                latitude = self._to_float(rec.get('latitude'))
                longitude = self._to_float(rec.get('longitude'))
                # Accept age -> date_of_birth conversion if provided
                date_of_birth = None
                age_val = rec.get('age')
                if age_val not in (None, ''):
                    try:
                        from datetime import date, timedelta
                        years = int(str(age_val).strip())
                        # Approximate: age years ago from mid-year
                        date_of_birth = date.today() - timedelta(days=years * 365)
                    except Exception:
                        date_of_birth = None

                user, was_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'gender': gender,
                        'bio': bio,
                        'location': location,
                        'phone_number': phone_number,
                        'latitude': latitude,
                        'longitude': longitude,
                        'date_of_birth': date_of_birth,
                        'is_online': False,
                        'last_activity': timezone.now(),
                    }
                )

                if was_created:
                    user.set_password(default_password)
                    created += 1
                else:
                    # Update basic fields if provided
                    user.email = email or user.email
                    user.first_name = first_name or user.first_name
                    user.last_name = last_name or user.last_name
                    user.gender = gender or user.gender
                    user.bio = bio or user.bio
                    user.location = location or user.location
                    user.phone_number = phone_number or user.phone_number
                    user.latitude = latitude if latitude is not None else user.latitude
                    user.longitude = longitude if longitude is not None else user.longitude
                    if date_of_birth is not None:
                        user.date_of_birth = date_of_birth
                    updated += 1

                # Handle profile photo
                photo_url = rec.get('photo_url')
                photo_filename = rec.get('photo_filename') or rec.get('photo')
                content_file = None

                if photo_url:
                    content_file = self._download_image(photo_url)
                elif images_dir and photo_filename:
                    local_path = os.path.join(images_dir, photo_filename)
                    content_file = self._open_local_image(local_path)

                if content_file is not None:
                    # Save to storage (S3 if configured)
                    user.profile_picture.save(self._safe_name(username, photo_filename or 'profile.jpg'), content_file, save=False)

                user.save()
                self.stdout.write(self.style.SUCCESS(f'[{idx}] {"CREATED" if was_created else "UPDATED"} {username}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[{idx}] FAILED: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Seed finished. Created: {created}, Updated: {updated}, Total processed: {len(records)}'))

    # -------- Helpers --------
    def _load_records(self, path, ext):
        if ext == '.csv':
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return [row for row in reader]
        else:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'records' in data:
                    return data['records']
                if isinstance(data, list):
                    return data
                raise CommandError('Invalid JSON structure: expected list or {"records": [...]}')

    def _derive_username(self, rec):
        parts = [rec.get('first_name', ''), rec.get('last_name', '')]
        base = ''.join(p for p in parts if p).lower() or 'user'
        return base.replace(' ', '')

    def _open_local_image(self, path):
        # Normalize and try common extensions if missing
        candidates = [path]
        base, ext = os.path.splitext(path)
        if ext == '':
            candidates = [
                f"{base}.jpg",
                f"{base}.jpeg",
                f"{base}.png",
                f"{base}.JPG",
                f"{base}.JPEG",
                f"{base}.PNG",
            ]

        existing = next((p for p in candidates if os.path.exists(p)), None)
        if existing is None:
            raise CommandError(f'Image not found: {path}')

        with Image.open(existing) as img:
            img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            return ContentFile(buf.read(), name=os.path.basename(existing))

    def _download_image(self, url):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            content = resp.content
        except Exception as http_err:
            # If access to S3 is forbidden, try using boto3 with credentials
            if 'amazonaws.com' in url:
                s3_content = self._fetch_s3_object_bytes(url)
                if s3_content is None:
                    raise http_err
                content = s3_content
            else:
                raise http_err

        # Convert/normalize to JPEG to keep storage consistent
        try:
            img = Image.open(io.BytesIO(content)).convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            return ContentFile(buf.read(), name=os.path.basename(url) or 'profile.jpg')
        except Exception:
            # Fallback to raw bytes
            return ContentFile(content, name=os.path.basename(url) or 'profile.bin')

    def _fetch_s3_object_bytes(self, url):
        """Fetch object bytes from S3 using boto3 when the object is private."""
        try:
            import boto3
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # URL like: https://<bucket>.s3.<region>.amazonaws.com/<key>
            host = parsed.netloc  # <bucket>.s3.<region>.amazonaws.com
            path = parsed.path.lstrip('/')  # key
            bucket = host.split('.s3.')[0]
            s3 = boto3.client('s3',
                              aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                              region_name=os.getenv('AWS_S3_REGION_NAME'))
            obj = s3.get_object(Bucket=bucket, Key=path)
            return obj['Body'].read()
        except Exception:
            return None

    def _safe_name(self, username, filename):
        base = os.path.splitext(os.path.basename(filename))[0] if filename else 'profile'
        return f'profiles/{username}_{base}.jpg'

    def _to_float(self, value):
        try:
            if value in (None, ''):
                return None
            return float(str(value).replace(',', '.'))
        except Exception:
            return None


