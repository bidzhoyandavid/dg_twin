from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from .models import User
import openai
from PIL import Image
import io
import base64
import json
from django.contrib import messages

openai.api_key = settings.OPENAI_API_KEY

def home(request):
    return render(request, 'avatar/upload.html')

def restore_user(request, user_id):
    """
    Retrieve and display a user's avatar data by their ID.
    """
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user,
            'has_voice': bool(user.original_voice),
            'voice_url': user.original_voice.url if user.original_voice else None,
        }
        return render(request, 'avatar/restore.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('avatar:home')

def upload_photo(request):
    if request.method == 'POST':
        photo = request.FILES.get('photo')
        if not photo:
            return JsonResponse({'error': 'No photo provided'}, status=400)
        
        # Create new user instance
        user = User.objects.create(
            original_photo=photo,
            status='pending'
        )
        
        try:
            # Generate avatar using DALL-E
            user.status = 'processing'
            user.save()
            
            # Prepare the image for DALL-E
            img = Image.open(user.original_photo)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Generate avatar using DALL-E
            response = openai.images.create_variation(
                image=img_byte_arr,
                n=1,
                size="1024x1024"
            )
            
            # Save the generated avatar
            avatar_url = response.data[0].url
            user.save_generated_avatar_from_url(avatar_url)
            user.status = 'completed'
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'user_id': str(user.id),
                'generated_avatar_url': user.generated_avatar.url
            })
            
        except Exception as e:
            user.status = 'failed'
            user.error_message = str(e)
            user.save()
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'avatar/upload.html')

@require_http_methods(["POST"])
def record_voice(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        voice_data = request.POST.get('voice')
        
        if not voice_data:
            return JsonResponse({'error': 'No voice data provided'}, status=400)
            
        if voice_data.startswith('data:audio/'):
            # Extract the base64 encoded data
            format, base64_str = voice_data.split(';base64,')
            voice_data = base64.b64decode(base64_str)
            
            # Save the voice recording
            voice_filename = f"original_voice_{user.id}.wav"
            user.original_voice.save(voice_filename, ContentFile(voice_data), save=True)
            
            return JsonResponse({
                'status': 'success',
                'user_id': str(user.id),
                'voice_url': user.original_voice.url
            })
        else:
            return JsonResponse({'error': 'Invalid voice data format'}, status=400)
            
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def save_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_saved = True
        user.save()
        return JsonResponse({
            'status': 'success',
            'message': 'User saved successfully'
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def avatar_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'status': user.status,
            'generated_avatar_url': user.generated_avatar.url if user.generated_avatar else None,
            'has_voice': bool(user.original_voice),
            'voice_url': user.original_voice.url if user.original_voice else None,
            'error_message': user.error_message,
            'is_saved': user.is_saved
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
