import os
import io
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def process_and_recode_image(image_file, max_size=(1024, 1024), quality=85):
    """
    Process and recode an image to ensure it's in a Flutter-compatible format.
    
    Args:
        image_file: The uploaded image file
        max_size: Maximum dimensions (width, height)
        quality: JPEG quality (1-100)
    
    Returns:
        Processed image file ready for upload
    """
    try:
        # Open the image
        with Image.open(image_file) as img:
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"Image resized to {img.size}")
            
            # Save as JPEG with specified quality
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Create a new file object
            processed_file = ContentFile(output.getvalue())
            
            logger.info(f"Image processed successfully: {img.size}, quality: {quality}")
            return processed_file
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise ValueError(f"Could not process image: {str(e)}")

def validate_image_format(image_file):
    """
    Validate that the image is in a supported format.
    
    Args:
        image_file: The uploaded image file
    
    Returns:
        bool: True if format is supported
    """
    try:
        with Image.open(image_file) as img:
            # Check if it's a supported format
            supported_formats = ['JPEG', 'PNG', 'WEBP']
            return img.format in supported_formats
    except Exception as e:
        logger.error(f"Error validating image format: {e}")
        return False

def get_image_info(image_file):
    """
    Get information about the image.
    
    Args:
        image_file: The uploaded image file
    
    Returns:
        dict: Image information
    """
    try:
        with Image.open(image_file) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
            }
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return None

