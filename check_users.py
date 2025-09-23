#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
django.setup()

from accounts.models import User

print(f"Total users: {User.objects.count()}")
print("First 5 users:")
for u in User.objects.all()[:5]:
    print(f"  {u.id}: {u.username} - {u.first_name} {u.last_name} - {u.location}")

print("\nUsers with profile pictures:")
for u in User.objects.filter(profile_picture__isnull=False)[:3]:
    print(f"  {u.id}: {u.username} - {u.profile_picture}")

