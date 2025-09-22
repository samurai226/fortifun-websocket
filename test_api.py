#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
django.setup()

from accounts.models import User
from matching.views import PotentialMatchesView
from django.test import RequestFactory

print("=== Testing Django API ===")

# Test 1: Check users in database
print(f"Total users in database: {User.objects.count()}")

# Test 2: Test the view directly
print("\n=== Testing PotentialMatchesView directly ===")
factory = RequestFactory()
request = factory.get('/api/v1/matching/potential-matches?page_size=3')
view = PotentialMatchesView()
view.request = request

try:
    queryset = view.get_queryset()
    print(f"Queryset count: {queryset.count()}")
    
    # Test serialization
    serializer = view.get_serializer(queryset[:3], many=True)
    data = serializer.data
    print(f"Serialized data count: {len(data)}")
    
    if data:
        print("First user data:")
        print(f"  ID: {data[0].get('id')}")
        print(f"  Username: {data[0].get('username')}")
        print(f"  Name: {data[0].get('first_name')} {data[0].get('last_name')}")
        print(f"  Location: {data[0].get('location')}")
        print(f"  Interests: {data[0].get('interests')}")
        
except Exception as e:
    print(f"Error in view: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test HTTP request
print("\n=== Testing HTTP request ===")
try:
    response = requests.get('http://localhost:8000/api/v1/matching/potential-matches?page_size=3', timeout=10)
    print(f"HTTP Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response data count: {len(data.get('results', []))}")
        if data.get('results'):
            print("First result:")
            print(f"  ID: {data['results'][0].get('id')}")
            print(f"  Username: {data['results'][0].get('username')}")
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"HTTP request error: {e}")