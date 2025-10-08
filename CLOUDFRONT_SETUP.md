# CloudFront CDN Setup Guide

## Overview

This guide explains how to set up Amazon CloudFront CDN for the FortiFun dating app to serve static assets, media files, and profile pictures with optimal performance and global distribution.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Python 3.7+ with boto3 installed
- Django project with static/media files
- Flutter app ready for CDN integration

## Architecture

```
Flutter App → CloudFront CDN → S3 Bucket
                ↓
            Global Edge Locations
                ↓
            Faster Content Delivery
```

## Step 1: AWS Setup

### 1.1 Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-west-2)
- Default output format (json)

### 1.2 Create S3 Bucket

```bash
# Create S3 bucket for assets
aws s3 mb s3://fortu-app-assets-dev --region us-west-2

# Enable public read access
aws s3api put-bucket-policy --bucket fortu-app-assets-dev --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::fortu-app-assets-dev/*"
    }
  ]
}'
```

## Step 2: CloudFront Distribution

### 2.1 Create Distribution

```bash
# Run the deployment script
python deploy_cloudfront.py --create-bucket --create-distribution --upload-files
```

Or manually create via AWS Console:

1. Go to CloudFront in AWS Console
2. Click "Create Distribution"
3. Select "Web" delivery method
4. Configure origin:
   - Origin Domain: `fortu-app-assets-dev.s3.us-west-2.amazonaws.com`
   - Origin Path: (leave empty)
5. Configure default cache behavior:
   - Viewer Protocol Policy: Redirect HTTP to HTTPS
   - Allowed HTTP Methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
   - Cache Policy: CachingOptimized
6. Configure distribution settings:
   - Price Class: Use All Edge Locations
   - Alternate Domain Names: (optional)
   - SSL Certificate: Default CloudFront Certificate
7. Click "Create Distribution"

### 2.2 Wait for Deployment

CloudFront distributions take 15-20 minutes to deploy. Monitor the status in the AWS Console.

## Step 3: Django Configuration

### 3.1 Install Dependencies

```bash
pip install boto3 django-storages
```

### 3.2 Update Settings

Add to your `settings.py`:

```python
# CloudFront CDN Configuration
CLOUDFRONT_DISTRIBUTION_ID = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', 'd1234567890.cloudfront.net')

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'fortu-app-assets-dev')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
AWS_S3_CUSTOM_DOMAIN = CLOUDFRONT_DOMAIN
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 24 hours default
}
AWS_DEFAULT_ACL = 'public-read'

# Static and Media files with CloudFront
if CLOUDFRONT_DOMAIN:
    STATIC_URL = f'https://{CLOUDFRONT_DOMAIN}/static/'
    MEDIA_URL = f'https://{CLOUDFRONT_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
```

### 3.3 Environment Variables

Create `.env` file:

```bash
# CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID=E1234567890
CLOUDFRONT_DOMAIN=d1234567890.cloudfront.net

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=fortu-app-assets-dev
AWS_S3_REGION_NAME=us-west-2
```

### 3.4 Collect and Upload Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput

# Upload to S3
python manage.py setup_cloudfront --upload-files
```

## Step 4: Flutter Configuration

### 4.1 Add CloudFront Service

The `CloudFrontService` is already created in `lib/app/core/services/cloudfront_service.dart`.

### 4.2 Update Profile Controller

Profile pictures now use CloudFront URLs automatically.

### 4.3 Register Service

Add to your service initialization:

```dart
// In main.dart or service initialization
Get.put(CloudFrontService());
```

### 4.4 Use in Widgets

```dart
// Get CloudFront service
final cloudfront = Get.find<CloudFrontService>();

// Get optimized image URL
String imageUrl = cloudfront.getOptimizedImageUrl(
  'profil/user_123.jpg',
  width: 200,
  height: 200,
  quality: 85,
);

// Use in Image widget
Image.network(imageUrl)
```

## Step 5: Testing

### 5.1 Test Static Files

```bash
# Test static file access
curl https://d1234567890.cloudfront.net/static/css/main.css

# Test media file access
curl https://d1234567890.cloudfront.net/media/profil/user_123.jpg
```

### 5.2 Test from Flutter

```dart
// Test CloudFront service
final cloudfront = Get.find<CloudFrontService>();
String url = cloudfront.getCloudFrontUrl('profil/test.jpg');
print('CloudFront URL: $url');
```

### 5.3 Performance Testing

```bash
# Test from different locations
curl -w "@curl-format.txt" -o /dev/null -s "https://d1234567890.cloudfront.net/static/css/main.css"

# Create curl-format.txt:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                      ----------\n
#           time_total:  %{time_total}\n
```

## Step 6: Cache Management

### 6.1 Invalidate Cache

```bash
# Invalidate all files
python manage.py setup_cloudfront --invalidate-cache

# Invalidate specific paths
python manage.py setup_cloudfront --invalidate-cache --paths /static/* /media/*

# Using AWS CLI
aws cloudfront create-invalidation --distribution-id E1234567890 --paths "/*"
```

### 6.2 Cache Headers

Different file types have different cache settings:

- **Static files**: 1 year (CSS, JS, fonts)
- **Images**: 24 hours (profile pictures, media)
- **Videos**: 1 hour (video content)
- **Documents**: 1 hour (PDFs, etc.)

## Step 7: Monitoring and Optimization

### 7.1 CloudWatch Metrics

Monitor these metrics in CloudWatch:

- **Requests**: Total requests to CloudFront
- **Bytes Downloaded**: Data transfer
- **4xx Error Rate**: Client errors
- **5xx Error Rate**: Server errors
- **Cache Hit Rate**: Cache effectiveness

### 7.2 Cost Optimization

- Use appropriate price class (US, Canada, Europe vs. All Edge Locations)
- Monitor data transfer costs
- Set up billing alerts
- Use S3 Intelligent Tiering for storage

### 7.3 Performance Optimization

- Enable compression
- Use appropriate cache behaviors
- Set up custom error pages
- Monitor cache hit rates

## Step 8: Security

### 8.1 HTTPS Only

All CloudFront distributions use HTTPS by default.

### 8.2 Access Control

```python
# Restrict access to certain files
def get_signed_url(file_path, expiration=3600):
    """Generate signed URL for private files"""
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'fortu-app-assets-dev', 'Key': file_path},
        ExpiresIn=expiration
    )
```

### 8.3 CORS Configuration

```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": ["https://yourdomain.com"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### 1. 403 Forbidden Errors
- Check S3 bucket policy
- Verify file permissions
- Ensure CloudFront has access to S3

#### 2. 404 Not Found Errors
- Verify file exists in S3
- Check CloudFront origin configuration
- Wait for cache invalidation

#### 3. Slow Performance
- Check cache hit rates
- Verify edge location selection
- Monitor CloudWatch metrics

#### 4. CORS Issues
- Configure CORS on S3 bucket
- Check CloudFront CORS settings
- Verify allowed origins

### Debug Commands

```bash
# Check S3 bucket contents
aws s3 ls s3://fortu-app-assets-dev --recursive

# Check CloudFront distribution status
aws cloudfront get-distribution --id E1234567890

# Test CloudFront from command line
curl -I https://d1234567890.cloudfront.net/static/css/main.css

# Check cache headers
curl -H "Cache-Control: no-cache" https://d1234567890.cloudfront.net/static/css/main.css
```

## Cost Estimation

### CloudFront Costs (US East)

- **Data Transfer Out**: $0.085 per GB (first 10TB)
- **HTTP Requests**: $0.0075 per 10,000 requests
- **HTTPS Requests**: $0.0100 per 10,000 requests

### S3 Costs (US West 2)

- **Storage**: $0.023 per GB per month
- **Requests**: $0.0004 per 1,000 PUT requests
- **Data Transfer**: $0.09 per GB (to CloudFront)

### Example Monthly Costs

For a medium-sized app:
- 100GB storage: ~$2.30
- 1TB data transfer: ~$85
- 1M requests: ~$10
- **Total**: ~$100/month

## Best Practices

1. **Use appropriate cache behaviors** for different file types
2. **Monitor costs** and set up billing alerts
3. **Implement cache invalidation** for critical updates
4. **Use compression** to reduce data transfer
5. **Set up monitoring** with CloudWatch
6. **Test from different locations** to verify performance
7. **Keep CloudFront and S3 in the same region** when possible
8. **Use versioning** for static assets to enable long-term caching

## Next Steps

1. Set up monitoring and alerting
2. Configure custom domain (optional)
3. Implement image optimization
4. Set up automated deployments
5. Monitor and optimize costs
6. Implement CDN for API responses (if needed)

## Support

For issues with this setup:

1. Check AWS CloudFront documentation
2. Review CloudWatch logs and metrics
3. Test with curl commands
4. Verify S3 bucket permissions
5. Check CloudFront distribution status

## Environment Variables Summary

```bash
# Required
CLOUDFRONT_DISTRIBUTION_ID=E1234567890
CLOUDFRONT_DOMAIN=d1234567890.cloudfront.net
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=fortu-app-assets-dev
AWS_S3_REGION_NAME=us-west-2

# Optional
REDIS_URL=redis://localhost:6379
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```


