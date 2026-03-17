import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from .forms import VideoUploadForm
from .models import Video
from .tasks import process_transcription
from .exports import export_txt, export_srt

### AUTH VIEWS ###
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome.')
            return redirect('upload_video')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('upload_video')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
@require_POST
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

### VIDEO VIEWS ###
@login_required
def upload_video(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.user = request.user
            original_name = os.path.basename(video.file.name)
            video.title = os.path.splitext(original_name)[0] or 'Untitled'
            video.status = 'pending'
            video.save()
            model_size = form.cleaned_data.get('model_size', 'small')
            process_transcription.delay(video.id, model_size)
            messages.success(request, f'"{video.title}" uploaded successfully! Transcription is in progress.')
            return redirect('video_list')
    else:
        form = VideoUploadForm()
    
    return render(request, 'upload.html', {'form': form})

@login_required
def video_list(request):
    video_qs = Video.objects.filter(user=request.user).order_by('-uploaded_at')
    paginator = Paginator(video_qs, 6)
    page_number = request.GET.get('page')
    videos = paginator.get_page(page_number)
    return render(request, 'video_list.html', {'videos': videos})

@login_required
def video_detail(request, video_id):
    video = get_object_or_404(Video, id=video_id, user = request.user)
    return render(request, 'video_detail.html', {'video': video})


@login_required
@require_POST
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    title = video.title
    if video.file and video.file.storage.exists(video.file.name):
        video.file.delete(save=False)
    video.delete()
    messages.success(request, f'"{title}" has been deleted.')
    return redirect('video_list')


@login_required
def video_status(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    return JsonResponse({
        'status': video.status,
        'is_done': video.status in ('completed', 'failed'),
    })


@login_required
def download_transcript(request, video_id, fmt):
    video = get_object_or_404(Video, id=video_id, user=request.user)

    if video.status != 'completed':
        raise Http404("Transcript not available.")

    if fmt == 'txt':
        content = export_txt(video)
        content_type = 'text/plain'
        ext = 'txt'
    elif fmt == 'srt':
        content = export_srt(video)
        content_type = 'application/x-subrip'
        ext = 'srt'
    else:
        raise Http404("Unsupported format.")

    response = HttpResponse(content, content_type=content_type)
    filename = f"{slugify(video.title)}.{ext}"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
