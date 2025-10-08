# Add this new view to the existing views.py file

@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # For testing
def reprocess_all_images(request):
    """
    Reprocess all existing profile pictures to ensure Flutter compatibility.
    This is a temporary endpoint for fixing existing images.
    """
    try:
        from django.contrib.auth import get_user_model
        from .image_processing import process_and_recode_image, validate_image_format, get_image_info
        
        User = get_user_model()
        users = User.objects.filter(profile_picture__isnull=False)
        
        processed_count = 0
        error_count = 0
        results = []
        
        for user in users:
            try:
                if not user.profile_picture:
                    continue
                
                # Get original image info
                original_info = get_image_info(user.profile_picture)
                
                # Validate current image
                if not validate_image_format(user.profile_picture):
                    results.append({
                        'user_id': user.id,
                        'status': 'skipped',
                        'reason': 'invalid_format',
                        'original_info': original_info
                    })
                    continue
                
                # Process and recode the image
                processed_file = process_and_recode_image(
                    user.profile_picture, 
                    max_size=(1024, 1024), 
                    quality=85
                )
                
                # Save the processed image
                user.profile_picture = processed_file
                user.save(update_fields=['profile_picture'])
                
                processed_count += 1
                results.append({
                    'user_id': user.id,
                    'status': 'processed',
                    'original_info': original_info
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'user_id': user.id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return Response({
            'message': 'Image reprocessing complete',
            'total_users': users.count(),
            'processed_count': processed_count,
            'error_count': error_count,
            'results': results
        })
        
    except Exception as e:
        return Response({
            'error': f'Reprocessing failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)