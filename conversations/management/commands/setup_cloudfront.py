# conversations/management/commands/setup_cloudfront.py

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from conversations.services.cloudfront_service import cloudfront_service
from cloudfront_config import CloudFrontConfig

class Command(BaseCommand):
    help = 'Setup CloudFront CDN for FortiFun app'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-distribution',
            action='store_true',
            help='Create a new CloudFront distribution',
        )
        parser.add_argument(
            '--list-distributions',
            action='store_true',
            help='List existing CloudFront distributions',
        )
        parser.add_argument(
            '--invalidate-cache',
            action='store_true',
            help='Invalidate CloudFront cache',
        )
        parser.add_argument(
            '--paths',
            nargs='+',
            help='Paths to invalidate (for --invalidate-cache)',
        )
        parser.add_argument(
            '--distribution-id',
            type=str,
            help='CloudFront distribution ID',
        )
        parser.add_argument(
            '--origin-domain',
            type=str,
            help='Origin domain for new distribution',
        )
    
    def handle(self, *args, **options):
        if options['list_distributions']:
            self.list_distributions()
        elif options['create_distribution']:
            self.create_distribution(options)
        elif options['invalidate_cache']:
            self.invalidate_cache(options)
        else:
            self.show_help()
    
    def list_distributions(self):
        """List existing CloudFront distributions"""
        self.stdout.write("Fetching CloudFront distributions...")
        
        try:
            import boto3
            cloudfront = boto3.client('cloudfront')
            
            response = cloudfront.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])
            
            if not distributions:
                self.stdout.write(self.style.WARNING("No distributions found"))
                return
            
            self.stdout.write(f"\nFound {len(distributions)} distribution(s):")
            self.stdout.write("-" * 80)
            
            for dist in distributions:
                self.stdout.write(f"ID: {dist['Id']}")
                self.stdout.write(f"Domain: {dist['DomainName']}")
                self.stdout.write(f"Status: {dist['Status']}")
                self.stdout.write(f"Enabled: {dist['Enabled']}")
                self.stdout.write(f"Comment: {dist.get('Comment', 'N/A')}")
                self.stdout.write("-" * 80)
                
        except Exception as e:
            raise CommandError(f"Error listing distributions: {e}")
    
    def create_distribution(self, options):
        """Create a new CloudFront distribution"""
        origin_domain = options.get('origin_domain')
        
        if not origin_domain:
            # Use S3 bucket as origin
            origin_domain = f"{CloudFrontConfig.S3_BUCKET_NAME}.s3.{CloudFrontConfig.S3_REGION}.amazonaws.com"
        
        self.stdout.write(f"Creating CloudFront distribution with origin: {origin_domain}")
        
        try:
            distribution = cloudfront_service.create_distribution(
                origin_domain=origin_domain,
                comment="FortiFun CDN Distribution"
            )
            
            if distribution:
                self.stdout.write(self.style.SUCCESS("Distribution created successfully!"))
                self.stdout.write(f"Distribution ID: {distribution['Id']}")
                self.stdout.write(f"Domain Name: {distribution['DomainName']}")
                self.stdout.write(f"Status: {distribution['Status']}")
                self.stdout.write("\nNote: It may take 15-20 minutes for the distribution to be fully deployed.")
            else:
                self.stdout.write(self.style.ERROR("Failed to create distribution"))
                
        except Exception as e:
            raise CommandError(f"Error creating distribution: {e}")
    
    def invalidate_cache(self, options):
        """Invalidate CloudFront cache"""
        distribution_id = options.get('distribution_id') or CloudFrontConfig.DISTRIBUTION_ID
        paths = options.get('paths', ['/*'])
        
        if not distribution_id:
            raise CommandError("Distribution ID is required. Use --distribution-id or set CLOUDFRONT_DISTRIBUTION_ID environment variable.")
        
        self.stdout.write(f"Invalidating cache for distribution: {distribution_id}")
        self.stdout.write(f"Paths: {', '.join(paths)}")
        
        try:
            success = cloudfront_service.invalidate_cache(paths)
            
            if success:
                self.stdout.write(self.style.SUCCESS("Cache invalidation initiated successfully!"))
                self.stdout.write("Note: It may take 5-15 minutes for the invalidation to complete.")
            else:
                self.stdout.write(self.style.ERROR("Failed to invalidate cache"))
                
        except Exception as e:
            raise CommandError(f"Error invalidating cache: {e}")
    
    def show_help(self):
        """Show help information"""
        self.stdout.write("CloudFront CDN Management Commands:")
        self.stdout.write("=" * 50)
        self.stdout.write("1. List distributions:")
        self.stdout.write("   python manage.py setup_cloudfront --list-distributions")
        self.stdout.write("")
        self.stdout.write("2. Create new distribution:")
        self.stdout.write("   python manage.py setup_cloudfront --create-distribution")
        self.stdout.write("   python manage.py setup_cloudfront --create-distribution --origin-domain your-bucket.s3.region.amazonaws.com")
        self.stdout.write("")
        self.stdout.write("3. Invalidate cache:")
        self.stdout.write("   python manage.py setup_cloudfront --invalidate-cache")
        self.stdout.write("   python manage.py setup_cloudfront --invalidate-cache --paths /static/* /media/*")
        self.stdout.write("   python manage.py setup_cloudfront --invalidate-cache --distribution-id E1234567890")
        self.stdout.write("")
        self.stdout.write("Environment Variables:")
        self.stdout.write("- CLOUDFRONT_DISTRIBUTION_ID: Your CloudFront distribution ID")
        self.stdout.write("- CLOUDFRONT_DOMAIN: Your CloudFront domain name")
        self.stdout.write("- AWS_ACCESS_KEY_ID: AWS access key")
        self.stdout.write("- AWS_SECRET_ACCESS_KEY: AWS secret key")
        self.stdout.write("- AWS_STORAGE_BUCKET_NAME: S3 bucket name")


