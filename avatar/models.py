from django.db import models
import uuid
import requests
from django.core.files.base import ContentFile

def user_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/avatars/<filename>
    return f'avatars/{filename}'

def voice_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/voices/<filename>
    return f'voices/{filename}'

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_photo = models.ImageField(upload_to=user_directory_path)
    generated_avatar = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    original_voice = models.FileField(upload_to=voice_directory_path, blank=True, null=True)
    generated_voice = models.FileField(upload_to=voice_directory_path, blank=True, null=True)
    prompt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    is_saved = models.BooleanField(default=False)  # New field to track if the user is saved

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"User {self.id} ({self.status})"

    def save_generated_avatar_from_url(self, url):
        """Download the image from DALL-E URL and save it to generated_avatar field"""
        if url and not self.generated_avatar:
            response = requests.get(url)
            if response.status_code == 200:
                # Create a filename for the downloaded image
                filename = f"generated_{self.id}.png"
                self.generated_avatar.save(filename, ContentFile(response.content), save=False)
                self.dall_e_url = url
                self.save()
