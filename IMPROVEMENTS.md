# Video Transcriber — Improvement Plan

A detailed, step-by-step plan to bring the project from its current state to a production-ready, secure, and well-architected Django application.

---

## Table of Contents

- [Phase 1: Critical Fixes](#phase-1-critical-fixes)
- [Phase 2: Security Hardening](#phase-2-security-hardening)
- [Phase 3: Architecture & Performance](#phase-3-architecture--performance)
- [Phase 4: Feature Enhancements](#phase-4-feature-enhancements)
- [Phase 5: Testing](#phase-5-testing)
- [Phase 6: DevOps & Deployment](#phase-6-devops--deployment)

---

## Phase 1: Critical Fixes

> These issues must be resolved first. The application is partially broken and has a data-exposure vulnerability without them.

### 1.1 Fix Media File Serving

**Problem:** `MEDIA_URL` and `MEDIA_ROOT` are not defined in `settings.py`. No URL pattern serves media files. Video playback via `{{ video.file.url }}` in templates is broken.

**Files to change:**
- `video_transcriber/video_transcriber/settings.py`
- `video_transcriber/video_transcriber/urls.py`

**Steps:**
1. Add to `settings.py`:
   ```python
   import os

   MEDIA_URL = '/media/'
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
   ```
2. Update `urls.py` to serve media in development:
   ```python
   from django.conf import settings
   from django.conf.urls.static import static

   urlpatterns = [
       # ... existing patterns ...
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```
3. Update the `Video` model's `FileField` — `upload_to='videos/'` will now save files to `media/videos/`.
4. Move any existing uploaded files from `videos/` to `media/videos/`.
5. Add `media/` to `.gitignore`.

---

### 1.2 Fix IDOR Vulnerability in `video_detail`

**Problem:** `video_detail` view fetches any video by ID without checking ownership. Any authenticated user can view any other user's video and transcript by guessing the URL (`/videos/1/`, `/videos/2/`, etc.).

**File to change:**
- `video_transcriber/transcription/views.py`

**Steps:**
1. Change the query in `video_detail` from:
   ```python
   video = get_object_or_404(Video, id=video_id)
   ```
   to:
   ```python
   video = get_object_or_404(Video, id=video_id, user=request.user)
   ```
   This ensures users can only access their own videos. Unauthorized access returns a 404.

---

### 1.3 Move Secret Key to Environment Variable

**Problem:** `SECRET_KEY` is hardcoded in `settings.py` with the `django-insecure-` prefix and is committed to version control.

**Files to change:**
- `video_transcriber/video_transcriber/settings.py`
- New file: `video_transcriber/.env`
- New file: `video_transcriber/.env.example`

**Steps:**
1. Install `python-decouple`:
   ```bash
   pip install python-decouple
   ```
2. Create a `.env` file in the Django project root (next to `manage.py`):
   ```
   SECRET_KEY=<generate-a-new-key>
   DEBUG=True
   ```
3. Create a `.env.example` for reference (committed to repo):
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```
4. Update `settings.py`:
   ```python
   from decouple import config

   SECRET_KEY = config('SECRET_KEY')
   DEBUG = config('DEBUG', default=False, cast=bool)
   ```
5. Add `.env` to `.gitignore`.
6. Generate a new secret key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
7. Add `python-decouple` to `requirements.txt`.

---

### 1.4 Remove Hardcoded Default on User ForeignKey

**Problem:** `models.ForeignKey(User, default=1)` assumes a user with `id=1` always exists. This could cause `IntegrityError` if used incorrectly.

**File to change:**
- `video_transcriber/transcription/models.py`

**Steps:**
1. Remove `default=1` from the `user` field:
   ```python
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   ```
2. Create and run a migration:
   ```bash
   python manage.py makemigrations transcription
   python manage.py migrate
   ```

---

## Phase 2: Security Hardening

> Protect the application against common attack vectors.

### 2.1 Add File Upload Validation

**Problem:** The upload form accepts any file type and any file size. Users could upload non-video files or excessively large files.

**Files to change:**
- `video_transcriber/transcription/forms.py`
- `video_transcriber/video_transcriber/settings.py`

**Steps:**
1. Add a `clean_file()` method to `VideoUploadForm`:
   ```python
   ALLOWED_VIDEO_TYPES = [
       'video/mp4', 'video/mpeg', 'video/quicktime',
       'video/x-msvideo', 'video/webm', 'video/ogg',
       'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac',
   ]
   MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

   def clean_file(self):
       file = self.cleaned_data.get('file')
       if file:
           if file.content_type not in self.ALLOWED_VIDEO_TYPES:
               raise forms.ValidationError('Unsupported file type. Please upload a video or audio file.')
           if file.size > self.MAX_FILE_SIZE:
               raise forms.ValidationError('File too large. Maximum size is 500 MB.')
       return file
   ```
2. Add a global upload limit in `settings.py`:
   ```python
   DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 MB
   FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760   # 10 MB (files above this are streamed to disk)
   ```

---

### 2.2 Add Rate Limiting on Authentication

**Problem:** No protection against brute-force login attempts.

**Files to change:**
- `requirements.txt`
- `video_transcriber/video_transcriber/settings.py`

**Steps:**
1. Install `django-axes`:
   ```bash
   pip install django-axes
   ```
2. Add `'axes'` to `INSTALLED_APPS`.
3. Add `'axes.backends.AxesStandaloneBackend'` to `AUTHENTICATION_BACKENDS`.
4. Add `'axes.middleware.AxesMiddleware'` to `MIDDLEWARE`.
5. Configure lockout settings:
   ```python
   AXES_FAILURE_LIMIT = 5
   AXES_COOLOFF_TIME = 1  # 1 hour lockout
   AXES_LOCKOUT_TEMPLATE = 'auth/lockout.html'
   ```
6. Create the `lockout.html` template.
7. Run `python manage.py migrate` (axes needs its own tables).

---

### 2.3 Add Security Headers for Production

**File to change:**
- `video_transcriber/video_transcriber/settings.py`

**Steps:**
Add the following settings (gated behind `DEBUG=False` or in a production settings file):
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True        # only for HTTPS
SESSION_COOKIE_SECURE = True     # only for HTTPS
SECURE_SSL_REDIRECT = True       # only for HTTPS
```

---

## Phase 3: Architecture & Performance

> The biggest impact changes — making transcription async and caching the model.

### 3.1 Add Status Field to Video Model

**Problem:** There is no way to track whether a video is pending, processing, completed, or failed.

**File to change:**
- `video_transcriber/transcription/models.py`

**Steps:**
1. Add a `status` field:
   ```python
   class Video(models.Model):
       STATUS_CHOICES = [
           ('pending', 'Pending'),
           ('processing', 'Processing'),
           ('completed', 'Completed'),
           ('failed', 'Failed'),
       ]

       user = models.ForeignKey(User, on_delete=models.CASCADE)
       title = models.CharField(max_length=255)
       file = models.FileField(upload_to='videos/')
       transcript = models.TextField(blank=True, null=True)
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
       uploaded_at = models.DateTimeField(auto_now_add=True)
   ```
2. Create and run a migration.
3. Update templates to show the status badge for each video.

---

### 3.2 Cache the Whisper Model (Singleton)

**Problem:** `whisper.load_model("small")` is called on every transcription request. The ~500 MB model is loaded from disk into memory each time.

**File to change:**
- `video_transcriber/transcription/utils.py`

**Steps:**
1. Refactor to use a module-level cached model:
   ```python
   import whisper

   _model = None

   def get_model(model_name="small"):
       global _model
       if _model is None:
           _model = whisper.load_model(model_name)
       return _model

   def transcribe_video(video_path):
       model = get_model()
       result = model.transcribe(video_path)
       return result['text']
   ```
2. Remove unused `os` and `settings` imports.

---

### 3.3 Add Celery for Asynchronous Transcription

**Problem:** Transcription runs synchronously inside the HTTP request. Long videos will cause request timeouts. Users have no progress feedback.

**New files:**
- `video_transcriber/video_transcriber/celery.py`
- `video_transcriber/transcription/tasks.py`

**Files to change:**
- `video_transcriber/video_transcriber/__init__.py`
- `video_transcriber/video_transcriber/settings.py`
- `video_transcriber/transcription/views.py`
- `video_transcriber/transcription/templates/video_detail.html`
- `requirements.txt`

**Steps:**
1. Install Celery and Redis:
   ```bash
   pip install celery redis
   ```
2. Create `celery.py` in the project config package:
   ```python
   import os
   from celery import Celery

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video_transcriber.settings')
   app = Celery('video_transcriber')
   app.config_from_object('django.conf:settings', namespace='CELERY')
   app.autodiscover_tasks()
   ```
3. Update `__init__.py`:
   ```python
   from .celery import app as celery_app
   __all__ = ('celery_app',)
   ```
4. Add Celery settings to `settings.py`:
   ```python
   CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
   CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
   ```
5. Create `tasks.py`:
   ```python
   from celery import shared_task
   from .models import Video
   from .utils import transcribe_video

   @shared_task
   def process_transcription(video_id):
       video = Video.objects.get(id=video_id)
       video.status = 'processing'
       video.save()
       try:
           transcript = transcribe_video(video.file.path)
           video.transcript = transcript
           video.status = 'completed'
       except Exception as e:
           video.status = 'failed'
       video.save()
   ```
6. Update `upload_video` view to queue the task instead of running synchronously:
   ```python
   if form.is_valid():
       video = form.save(commit=False)
       video.user = request.user
       video.status = 'pending'
       video.save()
       process_transcription.delay(video.id)
       return redirect('video_list')
   ```
7. Update templates to display status and auto-refresh when processing.
8. Add `celery` and `redis` to `requirements.txt`.
9. Update `.env.example`:
   ```
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

---

### 3.4 Store Transcript Segments with Timestamps

**Problem:** Only `result['text']` is saved, discarding segment-level timestamps and metadata that Whisper provides.

**Files to change:**
- `video_transcriber/transcription/models.py`
- `video_transcriber/transcription/utils.py`
- `video_transcriber/transcription/tasks.py`
- `video_transcriber/transcription/templates/video_detail.html`

**Steps:**
1. Add a `segments` JSONField to the `Video` model:
   ```python
   segments = models.JSONField(blank=True, null=True)
   ```
2. Update `transcribe_video()` to return both text and segments:
   ```python
   def transcribe_video(video_path):
       model = get_model()
       result = model.transcribe(video_path)
       segments = [
           {'start': s['start'], 'end': s['end'], 'text': s['text']}
           for s in result['segments']
       ]
       return result['text'], segments
   ```
3. Save segments in the Celery task.
4. Display clickable timestamps in `video_detail.html` using JavaScript to seek the `<video>` player.

---

## Phase 4: Feature Enhancements

### 4.1 Register Video Model in Django Admin

**File to change:**
- `video_transcriber/transcription/admin.py`

**Steps:**
```python
from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('transcript', 'uploaded_at')
```

---

### 4.2 Add Password Reset Flow

**Files to change:**
- `video_transcriber/transcription/urls.py`
- `video_transcriber/video_transcriber/settings.py`
- New templates: `auth/password_reset.html`, `auth/password_reset_done.html`, `auth/password_reset_confirm.html`, `auth/password_reset_complete.html`

**Steps:**
1. Add Django's built-in password reset views to `urls.py`:
   ```python
   from django.contrib.auth import views as auth_views

   urlpatterns += [
       path('password-reset/', auth_views.PasswordResetView.as_view(
           template_name='auth/password_reset.html'), name='password_reset'),
       path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
           template_name='auth/password_reset_done.html'), name='password_reset_done'),
       path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
           template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
       path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
           template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
   ]
   ```
2. Configure email backend in `settings.py` (console backend for development):
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   ```
3. Create the four password reset templates extending `base.html`.
4. Add a "Forgot Password?" link on the login page.

---

### 4.3 Add Whisper Model Size Selection

**Problem:** The Whisper model size is hardcoded to `"small"`. Users may want to trade speed for accuracy.

**Files to change:**
- `video_transcriber/transcription/forms.py`
- `video_transcriber/transcription/views.py`
- `video_transcriber/transcription/utils.py`
- `video_transcriber/transcription/templates/upload.html`

**Steps:**
1. Add a `model_size` choice field to the upload form:
   ```python
   MODEL_CHOICES = [
       ('tiny', 'Tiny (fastest, least accurate)'),
       ('base', 'Base'),
       ('small', 'Small (default)'),
       ('medium', 'Medium'),
       ('large', 'Large (slowest, most accurate)'),
   ]
   model_size = forms.ChoiceField(choices=MODEL_CHOICES, initial='small')
   ```
2. Pass the selected model size through to the transcription task.
3. Update the caching logic to handle multiple model sizes.

---

### 4.4 Add Transcript Export (TXT, SRT)

**New file:**
- `video_transcriber/transcription/exports.py`

**Files to change:**
- `video_transcriber/transcription/views.py`
- `video_transcriber/transcription/urls.py`
- `video_transcriber/transcription/templates/video_detail.html`

**Steps:**
1. Create export utility functions in `exports.py`:
   - `export_txt(video)` — plain text download
   - `export_srt(video)` — SubRip subtitle format (requires segment timestamps from 3.4)
2. Create a `download_transcript` view:
   ```python
   def download_transcript(request, video_id, format):
       video = get_object_or_404(Video, id=video_id, user=request.user)
       # return HttpResponse with appropriate content_type and Content-Disposition
   ```
3. Add URL pattern: `videos/<int:video_id>/download/<str:format>/`
4. Add download buttons on the video detail template.

---

### 4.5 Improve the UI/UX

**Files to change:**
- All templates in `video_transcriber/transcription/templates/`

**Steps:**
1. Add Django messages framework support in `base.html`:
   ```html
   {% if messages %}
   <div class="container mt-3">
       {% for message in messages %}
       <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
           {{ message }}
           <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
       </div>
       {% endfor %}
   </div>
   {% endif %}
   ```
2. Add flash messages in views for success/error feedback.
3. Add a loading spinner or progress message on the upload page while the form submits.
4. Display status badges (Pending/Processing/Completed/Failed) on `video_list.html`.
5. Add pagination to `video_list` if the user has many videos.

---

## Phase 5: Testing

### 5.1 Write Unit and Integration Tests

**File to change:**
- `video_transcriber/transcription/tests.py`

**Test plan:**

| Test Category | What to Test |
|---|---|
| **Model Tests** | Video creation, `__str__`, status field defaults, user association |
| **Form Tests** | Valid submission, missing fields, invalid file type, oversized file |
| **View Tests — Auth** | Register creates user, login works, logout redirects, unauthenticated redirects to login |
| **View Tests — Upload** | Authenticated upload saves file, sets user, queues task |
| **View Tests — Authorization** | User cannot access another user's video (returns 404) |
| **View Tests — List** | Only shows current user's videos |
| **Utility Tests** | `transcribe_video()` returns text (mock Whisper for unit tests) |
| **Task Tests** | Celery task updates status and saves transcript (mock Whisper) |

**Steps:**
1. Write tests using `django.test.TestCase` and `django.test.Client`.
2. Use `unittest.mock.patch` to mock Whisper model (avoid loading ML model in tests).
3. Use `SimpleUploadedFile` for file upload tests.
4. Aim for coverage of all views and the critical utility path.

---

### 5.2 Add a pytest Configuration (Optional)

**New files:**
- `pytest.ini` or `pyproject.toml` section
- `conftest.py`

**Steps:**
1. Install `pytest-django`:
   ```bash
   pip install pytest-django
   ```
2. Configure in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   DJANGO_SETTINGS_MODULE = "video_transcriber.settings"
   python_files = ["tests.py", "test_*.py"]
   ```

---

## Phase 6: DevOps & Deployment

### 6.1 Docker Setup

**New files:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

**Steps:**
1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   RUN apt-get update && apt-get install -y ffmpeg
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["gunicorn", "video_transcriber.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```
2. Create `docker-compose.yml` with services:
   - `web` — Django app (gunicorn)
   - `redis` — Message broker for Celery
   - `celery` — Celery worker for transcription tasks
3. Create `.dockerignore` to exclude `venv/`, `__pycache__/`, `.env`, `db.sqlite3`, `media/`.

---

### 6.2 Split Settings for Environments

**New files:**
- `video_transcriber/video_transcriber/settings/base.py`
- `video_transcriber/video_transcriber/settings/development.py`
- `video_transcriber/video_transcriber/settings/production.py`

**Steps:**
1. Move common settings to `base.py`.
2. `development.py` imports from `base.py` and sets `DEBUG=True`, SQLite, console email backend.
3. `production.py` imports from `base.py` and sets `DEBUG=False`, PostgreSQL, security headers, proper `ALLOWED_HOSTS`.
4. Update `manage.py` and `wsgi.py` to use the appropriate settings module (controlled by env var).

---

### 6.3 Add GitHub Actions CI Pipeline

**New file:**
- `.github/workflows/ci.yml`

**Steps:**
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: sudo apt-get install -y ffmpeg
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-django
      - run: cd video_transcriber && python manage.py test
```

---

### 6.4 Clean Up Dependencies

**File to change:**
- `requirements.txt`

**Steps:**
1. Remove `SpeechRecognition` — imported nowhere in the codebase.
2. Consider splitting into:
   - `requirements.txt` — core production dependencies only
   - `requirements-dev.txt` — adds pytest, coverage, flake8, etc.
3. Pin all versions for reproducibility.

---

### 6.5 Add `STATIC_ROOT` for Production

**File to change:**
- `video_transcriber/video_transcriber/settings.py`

**Steps:**
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```
Run `python manage.py collectstatic` before deployment.

---

## Summary Checklist

| # | Task | Phase | Priority |
|---|------|-------|----------|
| 1.1 | Fix media file serving | 1 | P0 |
| 1.2 | Fix IDOR in video_detail | 1 | P0 |
| 1.3 | Move secret key to .env | 1 | P0 |
| 1.4 | Remove hardcoded user default | 1 | P0 |
| 2.1 | Add file upload validation | 2 | P1 |
| 2.2 | Add rate limiting on auth | 2 | P1 |
| 2.3 | Add security headers | 2 | P1 |
| 3.1 | Add status field to Video | 3 | P1 |
| 3.2 | Cache Whisper model | 3 | P1 |
| 3.3 | Add Celery for async transcription | 3 | P2 |
| 3.4 | Store transcript segments | 3 | P2 |
| 4.1 | Register model in admin | 4 | P1 |
| 4.2 | Add password reset flow | 4 | P2 |
| 4.3 | Add model size selection | 4 | P3 |
| 4.4 | Add transcript export | 4 | P3 |
| 4.5 | Improve UI/UX | 4 | P3 |
| 5.1 | Write tests | 5 | P2 |
| 5.2 | Add pytest config | 5 | P3 |
| 6.1 | Docker setup | 6 | P2 |
| 6.2 | Split settings | 6 | P2 |
| 6.3 | Add CI pipeline | 6 | P2 |
| 6.4 | Clean up dependencies | 6 | P1 |
| 6.5 | Add STATIC_ROOT | 6 | P1 |
