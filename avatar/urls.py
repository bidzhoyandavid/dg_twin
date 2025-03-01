from django.urls import path
from . import views

app_name = 'avatar'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload'),
    path('status/<uuid:user_id>/', views.avatar_status, name='status'),
    path('record-voice/<uuid:user_id>/', views.record_voice, name='record_voice'),
    path('save/<uuid:user_id>/', views.save_user, name='save_user'),
    path('restore/<uuid:user_id>/', views.restore_user, name='restore'),
] 