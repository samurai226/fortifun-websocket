#!/usr/bin/env python
"""
Minimal test to check if Django basic setup works
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Test basic imports
    from django.http import JsonResponse
    from django.utils import timezone
    
    print("✅ Basic imports successful")
    
    # Test minimal response
    response = JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'message': 'Backend is running'
    })
    
    print("✅ JsonResponse creation successful")
    print(f"Response content: {response.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
