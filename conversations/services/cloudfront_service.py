# conversations/services/cloudfront_service.py

import os
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from cloudfront_config import CloudFrontConfig, CloudFrontInvalidation

class CloudFrontService:
    """Service for managing CloudFront CDN operations"""
    
    def __init__(self):
        self.cloudfront = None
        self.s3 = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            # CloudFront client
            if CloudFrontConfig.DISTRIBUTION_ID:
                self.cloudfront = boto3.client('cloudfront')
            
            # S3 client
            self.s3 = boto3.client('s3')
            
        except Exception as e:
            print(f"Warning: Could not initialize AWS clients: {e}")
    
    def upload_file_to_s3(self, file_path, s3_key, content_type=None):
        """Upload file to S3 with proper metadata"""
        try:
            if not self.s3:
                return False
            
            # Determine content type
            if not content_type:
                content_type = self._get_content_type(file_path)
            
            # Get file type for cache headers
            file_type = CloudFrontConfig.get_file_type(s3_key)
            cache_headers = CloudFrontConfig.get_cache_headers(file_type)
            
            # Upload to S3
            with open(file_path, 'rb') as file:
                self.s3.upload_fileobj(
                    file,
                    CloudFrontConfig.S3_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': cache_headers['Cache-Control'],
                        'ACL': 'public-read'
                    }
                )
            
            print(f"File uploaded to S3: {s3_key}")
            return True
            
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error uploading to S3: {e}")
            return False
    
    def get_cloudfront_url(self, s3_key):
        """Get CloudFront URL for S3 key"""
        return CloudFrontConfig.get_cloudfront_url(s3_key)
    
    def get_optimized_image_url(self, s3_key, width=None, height=None, quality=85):
        """Get optimized image URL with transformations"""
        return CloudFrontConfig.get_optimized_url(s3_key, width, height, quality)
    
    def invalidate_cache(self, paths):
        """Invalidate CloudFront cache for given paths"""
        return CloudFrontInvalidation.create_invalidation(paths)
    
    def invalidate_user_media(self, user_id):
        """Invalidate all media for a user"""
        return CloudFrontInvalidation.invalidate_user_media(user_id)
    
    def invalidate_file(self, file_path):
        """Invalidate a specific file"""
        return CloudFrontInvalidation.invalidate_file(file_path)
    
    def _get_content_type(self, file_path):
        """Get content type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def get_distribution_info(self):
        """Get CloudFront distribution information"""
        try:
            if not self.cloudfront or not CloudFrontConfig.DISTRIBUTION_ID:
                return None
            
            response = self.cloudfront.get_distribution(
                Id=CloudFrontConfig.DISTRIBUTION_ID
            )
            
            distribution = response['Distribution']
            return {
                'id': distribution['Id'],
                'domain_name': distribution['DomainName'],
                'status': distribution['Status'],
                'enabled': distribution['Enabled'],
                'last_modified': distribution['LastModifiedTime'],
                'aliases': distribution.get('Aliases', {}).get('Items', []),
            }
            
        except ClientError as e:
            print(f"Error getting distribution info: {e}")
            return None
    
    def create_distribution(self, origin_domain, comment="FortiFun CDN Distribution"):
        """Create a new CloudFront distribution"""
        try:
            if not self.cloudfront:
                return None
            
            distribution_config = {
                'CallerReference': f"fortifun-{os.urandom(8).hex()}",
                'Comment': comment,
                'DefaultRootObject': 'index.html',
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': 'S3-Origin',
                        'DomainName': origin_domain,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'S3-Origin',
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    },
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,  # 24 hours
                    'MaxTTL': 31536000,  # 1 year
                },
                'Enabled': True,
                'PriceClass': 'PriceClass_100',  # US, Canada, Europe
            }
            
            response = self.cloudfront.create_distribution(
                DistributionConfig=distribution_config
            )
            
            return response['Distribution']
            
        except ClientError as e:
            print(f"Error creating distribution: {e}")
            return None
    
    def update_distribution(self, distribution_id, config_updates):
        """Update CloudFront distribution configuration"""
        try:
            if not self.cloudfront:
                return False
            
            # Get current config
            current = self.cloudfront.get_distribution_config(Id=distribution_id)
            config = current['DistributionConfig']
            etag = current['ETag']
            
            # Apply updates
            for key, value in config_updates.items():
                if key in config:
                    config[key] = value
            
            # Update distribution
            self.cloudfront.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            return True
            
        except ClientError as e:
            print(f"Error updating distribution: {e}")
            return False
    
    def delete_distribution(self, distribution_id):
        """Delete CloudFront distribution"""
        try:
            if not self.cloudfront:
                return False
            
            # Disable distribution first
            current = self.cloudfront.get_distribution_config(Id=distribution_id)
            config = current['DistributionConfig']
            etag = current['ETag']
            
            config['Enabled'] = False
            
            self.cloudfront.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            # Wait for deployment to complete
            import time
            time.sleep(30)
            
            # Delete distribution
            self.cloudfront.delete_distribution(
                Id=distribution_id,
                IfMatch=etag
            )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting distribution: {e}")
            return False

# Global service instance
cloudfront_service = CloudFrontService()


