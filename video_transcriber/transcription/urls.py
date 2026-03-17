from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register, user_login, user_logout, upload_video, video_list, video_detail, video_status, download_transcript, delete_video

urlpatterns = [
    path('', upload_video, name='upload_video'),
    path('videos/', video_list, name='video_list'),
    path('videos/<int:video_id>/', video_detail, name='video_detail'),
    path('videos/<int:video_id>/status/', video_status, name='video_status'),
    path('videos/<int:video_id>/download/<str:fmt>/', download_transcript, name='download_transcript'),
    path('videos/<int:video_id>/delete/', delete_video, name='delete_video'),

    # Authentication URLs
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
