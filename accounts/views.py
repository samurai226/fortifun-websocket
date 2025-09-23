# accounts/views.py

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from .serializers import (
    UserSerializer, UserUpdateSerializer
)
from matching.models import UserPreference
import os

User = get_user_model()





class UserDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer les détails d'un utilisateur spécifique"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)







# Removed Appwrite-specific views - using standard Django authentication

# ===================== Flutter DjangoService compatibility =====================

class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name') or ''
        first_name = name.split(' ')[0] if name else ''
        last_name = ' '.join(name.split(' ')[1:]) if name and len(name.split(' ')) > 1 else ''

        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        username = email.split('@')[0]
        user = User.objects.create_user(username=username, email=email, password=password,
                                        first_name=first_name, last_name=last_name)
        # create defaults
        UserPreference.objects.get_or_create(user=user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if not user:
            return Response({'detail': 'invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


class UsersMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_permissions(self):
        # Temporarily allow unauthenticated GET for testing
        if self.request.method in ['GET']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_object(self):
        # If authenticated, return the real current user
        if self.request.user and self.request.user.is_authenticated:
            return self.request.user
        # Temporary fallback for testing without auth: return or create a test user
        fallback_user, _ = User.objects.get_or_create(
            username='test_user_dashboard',
            defaults={'email': 'test_dashboard@example.com'}
        )
        return fallback_user

    def put(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Temporarily allow any for testing
def upload_profile_picture(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'file required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For testing without authentication, create a test user
        if not request.user.is_authenticated:
            # User is already defined at the top of the file using get_user_model()
            test_user, created = User.objects.get_or_create(
                username='test_user_123',
                defaults={'email': 'test@example.com'}
            )
            user = test_user
        else:
            user = request.user
        
        # Save the file to the user's profile_picture field
        user.profile_picture = file
        user.save(update_fields=['profile_picture'])
        
        # Get the URL of the uploaded file
        if user.profile_picture:
            return Response({
                'detail': 'uploaded', 
                'url': user.profile_picture.url,
                'filename': user.profile_picture.name
            })
        else:
            return Response({'detail': 'upload failed - no file saved'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        import traceback
        error_details = str(e)
        traceback_str = traceback.format_exc()
        print(f"Upload error: {error_details}")
        print(f"Traceback: {traceback_str}")
        return Response({
            'detail': f'upload failed: {error_details}',
            'error': 'internal_server_error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_message_attachment(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': 'file required'}, status=status.HTTP_400_BAD_REQUEST)
    # In a full implementation, save to a MessageAttachment model or S3 and return URL
    # For now, reuse profile_picture storage path with a different name pattern is discouraged.
    # Return placeholder response for MVP compatibility
    return Response({'detail': 'uploaded', 'url': ''})

# Removed Appwrite webhook - using standard Django authentication

# Removed Appwrite sync function - using standard Django authentication

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def set_test_user_photo(request):
    token = request.headers.get('X-Seed-Token') or request.query_params.get('token')
    if token != os.getenv('SEED_TOKEN', 'seed-3f3e7d8d-7d8b-4a0a-9f7d-2a1c6f8b1d92'):
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
    try:
        import boto3, random, os
        bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        region = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
        if not bucket:
            return Response({'detail': 'missing_s3_config'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        s3 = boto3.client('s3', region_name=region)
        resp = s3.list_objects_v2(Bucket=bucket, Prefix='profil/')
        contents = resp.get('Contents', [])
        image_keys = [obj['Key'] for obj in contents if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if not image_keys:
            return Response({'detail': 'no_images_found'}, status=status.HTTP_404_NOT_FOUND)
        selected = random.choice(image_keys)
        user, _ = User.objects.get_or_create(username='test_user_dashboard', defaults={'email': 'test_dashboard@example.com'})
        # Assign S3 key directly to ImageField
        user.profile_picture = selected
        user.save(update_fields=['profile_picture'])
        # Build public URL
        domain = f"{bucket}.s3.{region}.amazonaws.com"
        url = f"https://{domain}/{selected}"
        return Response({'detail': 'ok', 'key': selected, 'url': url})
    except Exception as e:
        return Response({'detail': 'error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)