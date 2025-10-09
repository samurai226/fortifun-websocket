# cloudfront_config.py
"""
CloudFront CDN configuration for FortiFun app
Handles media file serving, caching, and distribution
"""

import os
from django.conf import settings

class CloudFrontConfig:
    """Configuration class for CloudFront CDN"""
    
    # CloudFront distribution settings
    DISTRIBUTION_ID = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
    CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', 'd1234567890.cloudfront.net')
    
    # S3 bucket settings
    S3_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'fortu-app-assets-dev')
    S3_REGION = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
    
    # Cache settings
    CACHE_TTL = {
        'images': 86400,      # 24 hours for profile pictures
        'media': 3600,        # 1 hour for other media
        'static': 31536000,   # 1 year for static assets
    }
    
    # File type configurations
    FILE_TYPES = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'videos': ['.mp4', '.mov', '.avi', '.webm'],
        'documents': ['.pdf', '.doc', '.docx', '.txt'],
        'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
    }
    
    @classmethod
    def get_cloudfront_url(cls, file_path):
        """Generate CloudFront URL for a file"""
        if not file_path:
            return None
            
        # Remove leading slash if present
        file_path = file_path.lstrip('/')
        
        # Determine if it's an S3 URL or local path
        if file_path.startswith('https://'):
            # Already a full URL, return as is
            return file_path
        elif file_path.startswith('s3://'):
            # S3 URL, convert to CloudFront
            s3_path = file_path.replace('s3://', '').split('/', 1)[1]
            return f"https://{cls.CLOUDFRONT_DOMAIN}/{s3_path}"
        else:
            # Local path, construct CloudFront URL
            return f"https://{cls.CLOUDFRONT_DOMAIN}/{file_path}"
    
    @classmethod
    def get_cache_headers(cls, file_type):
        """Get cache headers for different file types"""
        ttl = cls.CACHE_TTL.get(file_type, cls.CACHE_TTL['media'])
        
        return {
            'Cache-Control': f'max-age={ttl}, public',
            'Expires': None,  # Let CloudFront handle expiration
        }
    
    @classmethod
    def is_image_file(cls, filename):
        """Check if file is an image"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.FILE_TYPES['images']
    
    @classmethod
    def is_video_file(cls, filename):
        """Check if file is a video"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.FILE_TYPES['videos']
    
    @classmethod
    def get_file_type(cls, filename):
        """Get file type category"""
        ext = os.path.splitext(filename)[1].lower()
        
        for file_type, extensions in cls.FILE_TYPES.items():
            if ext in extensions:
                return file_type
        
        return 'media'
    
    @classmethod
    def get_optimized_url(cls, file_path, width=None, height=None, quality=None):
        """Get optimized CloudFront URL with image transformations"""
        if not cls.is_image_file(file_path):
            return cls.get_cloudfront_url(file_path)
        
        # For images, we can add transformation parameters
        # This would work with CloudFront Functions or Lambda@Edge
        base_url = cls.get_cloudfront_url(file_path)
        
        if width or height or quality:
            params = []
            if width:
                params.append(f'w_{width}')
            if height:
                params.append(f'h_{height}')
            if quality:
                params.append(f'q_{quality}')
            
            # Add transformation path
            if params:
                # Insert transformation before filename
                parts = base_url.split('/')
                filename = parts[-1]
                parts[-1] = f"transform/{'/'.join(params)}/{filename}"
                base_url = '/'.join(parts)
        
        return base_url

# CloudFront invalidation settings
class CloudFrontInvalidation:
    """Handle CloudFront cache invalidation"""
    
    @classmethod
    def create_invalidation(cls, paths):
        """Create CloudFront invalidation for given paths"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            if not CloudFrontConfig.DISTRIBUTION_ID:
                print("Warning: CLOUDFRONT_DISTRIBUTION_ID not set, skipping invalidation")
                return False
            
            cloudfront = boto3.client('cloudfront')
            
            # Ensure paths start with /
            invalidation_paths = [path if path.startswith('/') else f'/{path}' for path in paths]
            
            response = cloudfront.create_invalidation(
                DistributionId=CloudFrontConfig.DISTRIBUTION_ID,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(invalidation_paths),
                        'Items': invalidation_paths
                    },
                    'CallerReference': f"invalidation-{os.urandom(8).hex()}"
                }
            )
            
            print(f"CloudFront invalidation created: {response['Invalidation']['Id']}")
            return True
            
        except ClientError as e:
            print(f"Error creating CloudFront invalidation: {e}")
            return False
        except ImportError:
            print("boto3 not installed, skipping CloudFront invalidation")
            return False
    
    @classmethod
    def invalidate_user_media(cls, user_id):
        """Invalidate all media for a specific user"""
        paths = [
            f'/profil/user_{user_id}/*',
            f'/media/user_{user_id}/*',
        ]
        return cls.create_invalidation(paths)
    
    @classmethod
    def invalidate_file(cls, file_path):
        """Invalidate a specific file"""
        # Remove leading slash if present
        file_path = file_path.lstrip('/')
        return cls.create_invalidation([f'/{file_path}'])

# Django settings integration
def configure_cloudfront_settings():
    """Configure Django settings for CloudFront"""
    
    # Static files configuration
    STATIC_URL = f"https://{CloudFrontConfig.CLOUDFRONT_DOMAIN}/static/"
    
    # Media files configuration
    MEDIA_URL = f"https://{CloudFrontConfig.CLOUDFRONT_DOMAIN}/media/"
    
    # AWS S3 settings for CloudFront
    AWS_S3_CUSTOM_DOMAIN = CloudFrontConfig.CLOUDFRONT_DOMAIN
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 24 hours default
    }
    
    # File storage settings
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    
    return {
        'STATIC_URL': STATIC_URL,
        'MEDIA_URL': MEDIA_URL,
        'AWS_S3_CUSTOM_DOMAIN': AWS_S3_CUSTOM_DOMAIN,
        'AWS_S3_OBJECT_PARAMETERS': AWS_S3_OBJECT_PARAMETERS,
        'DEFAULT_FILE_STORAGE': DEFAULT_FILE_STORAGE,
        'STATICFILES_STORAGE': STATICFILES_STORAGE,
    }




