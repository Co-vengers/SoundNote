# SoundNote

A production-ready Django application for transcribing video and audio files using OpenAI's Whisper model, with containerization, async task processing, and comprehensive security features.

## Overview

Video Transcriber is a modern, full-featured web application for transcribing video and audio content. It leverages OpenAI's Whisper, a state-of-the-art speech recognition model, combined with Docker containerization, PostgreSQL, Celery async tasks, and strict security controls to provide a reliable, scalable platform for media transcription.

## Key Features

### Core Transcription
- **Multiple File Formats**: MP4, MPEG, MOV, AVI, WebM, OGG, MP3, WAV, FLAC
- **Long Video Support**: Automatic chunking for videos over 15 minutes
- **Configurable Models**: Tiny, Base, Small (default), Medium, Large (accuracy vs. speed tradeoff)
- **Timestamp Segments**: Per-utterance transcripts with precise timing
- **Multi-format Export**: Download as TXT (plaintext) or SRT (subtitles for video players)

### Architecture & Reliability
- **Docker Containerization**: Reproducible deployments with docker-compose
- **PostgreSQL Database**: Production-grade data persistence and concurrent access
- **Celery Task Queue**: Asynchronous transcription processing with Redis broker
- **Graceful Error Handling**: Automatic recovery from worker crashes and deleted records
- **Persistent Model Cache**: Pre-downloaded Whisper models survive container restarts

### Security
- **User Authentication**: Registration, login, password reset with email
- **Authorization**: Users can only access their own videos (prevents IDOR attacks)
- **Brute-force Protection**: Lock accounts after 5 failed login attempts (24-hour cooldown)
- **CSRF Protection**: All forms include CSRF tokens
- **Secure Cookies**: HTTPS-only cookies in production
- **Input Validation**: File type, size, and content-type validation

### User Experience
- **Real-time Status Updates**: AJAX polling shows transcription progress
- **Pagination**: Video list with 6 items per page
- **Bootstrap UI**: Responsive, mobile-friendly interface
- **User-friendly Titles**: Video filenames automatically used as titles
- **Progress Tracking**: Visual status indicators (Pending, Processing, Completed, Failed)

## Installation

### Prerequisites

- Docker & Docker Compose (recommended for production)
- Python 3.12+ (for local development)
- FFmpeg (for audio extraction from video files)

### Quick Start with Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/Co-vengers/video_transcriber.git
   cd video_transcriber
   ```

2. Create environment configuration:
   ```bash
   cp video_transcriber/.env.example video_transcriber/.env
   # Edit video_transcriber/.env with your settings
   ```

3. Build and start services:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Web UI: http://localhost:8000
   - Admin: http://localhost:8000/admin (superuser required)

5. Create admin user (optional, in another terminal):
   ```bash
   docker-compose exec -T web python manage.py createsuperuser
   ```

### Local Development Setup

If you prefer running locally without Docker:

1. Clone the repository:
   ```bash
   git clone https://github.com/Co-vengers/video_transcriber.git
   cd video_transcriber
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp video_transcriber/.env.example video_transcriber/.env
   # Edit .env with development settings (use SQLite for local dev)
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Start Redis (in separate terminal):
   ```bash
   # Using Homebrew on macOS:
   brew services start redis
   # Or run directly:
   redis-server
   ```

8. Start Celery worker (in separate terminal):
   ```bash
   cd video_transcriber
   celery -A video_transcriber worker --loglevel=info
   ```

9. Start Django development server:
   ```bash
   cd video_transcriber
   python manage.py runserver
   ```

10. Access at http://localhost:8000

## Usage

### Web Interface Workflow

#### 1. **Register / Login**
- Click "Register" to create a new account or "Login" with existing credentials
- Password reset available via email link
- Brute-force protection: Account locks after 5 failed attempts (24-hour cooldown)

#### 2. **Upload Video**
- Click "Upload Video" from main menu
- Select a video or audio file (max 500 MB)
- Supported formats: MP4, MPEG, MOV, AVI, WebM, OGG, MP3, WAV, FLAC
- Choose Whisper model size:
  - **Tiny**: Fastest, ~39M parameters, basic accuracy
  - **Base**: Balanced, ~74M parameters
  - **Small**: Default, ~244M parameters, good accuracy/speed tradeoff
  - **Medium**: Slower, ~769M parameters, better accuracy
  - **Large**: Slowest, ~1.5B parameters, highest accuracy
- Click "Upload" to start transcription

#### 3. **Monitor Progress**
- Videos appear in "Videos" list with status badge
- Status updates in real-time (Pending → Processing → Completed/Failed)
- Progress visible without page refresh

#### 4. **Download Transcripts**
Once transcription completes, download in multiple formats:
- **TXT**: Plain text transcript (copy/paste friendly)
- **SRT**: SubRip format with timestamps (import into video players)
  - Format: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
  - Compatible with VLC, YouTube, browser video players

#### 5. **Manage Videos**
- View all your transcribed videos with status
- Click video title to see full transcript and segments
- Delete videos to free up storage
- Videos are private (only you can see your transcripts)

### Admin Interface

Access Django admin at `/admin`:
- Manage user accounts
- View/filter transcription jobs by status and date  
- Search videos by title or username
- Monitor transcription history

### API Endpoints (for developers)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Upload form |
| `/videos/` | GET | List user's videos (paginated) |
| `/videos/<id>/` | GET | View transcript and segments |
| `/videos/<id>/status/` | GET | JSON status (for AJAX polling) |
| `/videos/<id>/download/<fmt>/` | GET | Download transcript (fmt: txt or srt) |
| `/videos/<id>/delete/` | POST | Delete video |
| `/register/` | GET/POST | User registration |
| `/login/` | GET/POST | User login |
| `/logout/` | POST | User logout |
| `/password-reset/` | GET/POST | Password reset flow |


## Architecture

### Technology Stack

- **Web Framework**: Django 5.1.7 (Python web framework)
- **Application Server**: Gunicorn 23.0.0 (production WSGI server)
- **Database**: PostgreSQL 16 (production relational database)
- **Message Broker**: Redis 7 (in-memory message queue)
- **Task Queue**: Celery 5.4.0 (asynchronous job processing)
- **ML/AI Engine**: OpenAI Whisper 20240930 (speech-to-text)
- **Containerization**: Docker & docker-compose (reproducible deployments)
- **Frontend**: Bootstrap 5 (responsive CSS framework)

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Web Service   │  │   Worker     │  │   Database   │   │
│  │   (Gunicorn)    │  │  (Celery)    │  │(PostgreSQL)  │   │
│  │   2 workers     │  │ concurrency=4│  │              │   │
│  └────────┬────────┘  └──────┬───────┘  └──────────────┘   │
│           │                   │                              │
│           └──────────┬────────┘                              │
│                      │                                       │
│              ┌───────▼────────┐                              │
│              │  Redis Broker  │                              │
│              │  (Task Queue)  │                              │
│              └────────────────┘                              │
│                                                               │
│            Persistent Volumes:                               │
│            - whisper_cache: /cache/whisper (461MB model)     │
│            - postgres_data: PostgreSQL data                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User uploads video** → Web service saves to `/media/videos/`
2. **Task is queued** → Gunicorn sends `process_transcription` task to Redis
3. **Worker picks up task** → Celery worker loads Whisper model (cached)
4. **Chunked transcription** → Long videos split into 10-minute chunks
5. **Results saved** → Transcripts and segments stored in PostgreSQL
6. **Frontend updates** → AJAX polling shows real-time status
7. **User downloads** → Download as TXT or SRT subtitle format

### Project Structure

```
video_transcriber/
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Multi-service orchestration
├── requirements.txt        # Python dependencies
├── CHANGES_DOCUMENTATION.md # Full changelog and rationale
│
├── video_transcriber/      # Django project config
│   ├── settings.py         # Django configuration
│   ├── urls.py             # Main URL routing
│   ├── wsgi.py             # WSGI application
│   ├── celery.py           # Celery configuration
│   └── __init__.py         # Celery import
│
├── transcription/          # Django app (main logic)
│   ├── models.py           # Video model with ownership
│   ├── views.py            # All HTTP view handlers
│   ├── urls.py             # App URL patterns
│   ├── forms.py            # VideoUploadForm with validation
│   ├── tasks.py            # Celery transcription task
│   ├── admin.py            # Django admin configuration
│   ├── utils.py            # Whisper transcription utilities
│   ├── exports.py          # TXT/SRT export functions
│   │
│   ├── management/
│   │   └── commands/
│   │       └── requeue_stale_transcriptions.py  # Stale task recovery
│   │
│   ├── migrations/         # Database schema versions
│   │   ├── 0001_initial.py
│   │   ├── 0002_video_user.py
│   │   ├── 0003_alter_video_file_alter_video_user.py
│   │   ├── 0004_video_status.py
│   │   ├── 0005_video_segments.py
│   │   └── 0006_fix_upload_to_path.py
│   │
│   ├── templates/          # HTML templates
│   │   ├── base.html       # Navigation, Bootstrap layout
│   │   ├── upload.html     # Video upload form
│   │   ├── video_list.html # Paginated video gallery
│   │   ├── video_detail.html # Transcript viewer, download
│   │   └── auth/           # Authentication templates
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── password_reset.html
│   │       └── lockout.html
│   │
│   ├── static/             # CSS, JS, fonts
│   │   └── transcription/
│   │       └── favicon.svg
│   │
│   └── tests.py            # Unit tests
│
├── media/                  # User uploads (not in repo)
│   └── videos/
│
├── .env.example            # Environment template
├── .python-version         # Python 3.12
├── .gitignore              # Excluded files
└── README.md               # This file
```

## Security Features

### Authentication & Authorization
- ✅ User registration with password validation
- ✅ Secure password reset via email
- ✅ CSRF tokens on all forms
- ✅ Permission checks (users can only access their own videos)
- ✅ IDOR prevention (returns 404 if accessing others' content)

### Attack Prevention
- ✅ Brute-force protection (5 failed attempts → 24-hour lockout)
- ✅ HTTPS-only cookies in production
- ✅ Secure cookie flags (HttpOnly, SameSite)
- ✅ Security headers (X-Frame-Options=DENY, X-Content-Type-Options=nosniff)
- ✅ SQL injection prevention (parameterized queries via ORM)

### Data Protection
- ✅ Environment-based secrets (not in code)
- ✅ File type validation (extension + MIME type)
- ✅ File size limits (500 MB max)
- ✅ Input sanitization on all forms
- ✅ Secure file storage outside web root

### Worker Reliability
- ✅ Graceful error handling (no crashes on deleted records)
- ✅ Task timeouts (1 hour hard, 55-minute soft)
- ✅ Auto-requeue on worker loss
- ✅ Automatic stale task recovery on startup
- ✅ Non-root worker process (nobody:nogroup)

## Environment Configuration

### Docker Setup (`.env` file)

```env
# Security
SECRET_KEY=your-secret-key-here

# Debug Mode (False in production)
DEBUG=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_ENGINE=postgres           # or 'sqlite' for development
DB_NAME=video_transcriber
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db                   # Docker service name
DB_PORT=5432

# Message Broker & Results
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Stale Task Recovery
STALE_PROCESSING_MINUTES=45   # How old before marking as stale
RECOVERY_MODEL_SIZE=small      # Model to use for requeue
```

### Email Configuration (Optional)

For password reset emails:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

## Performance & Deployment

### Performance Tips

- **GPU Support**: Using CUDA GPU significantly improves transcription speed
- **Model Selection**:
  - `tiny` (39M params): 5-10x faster, lower accuracy
  - `base` (74M params): 2-5x faster, decent accuracy
  - `small` (244M params): Default, good balance
  - `medium` (769M params): Slower, better accuracy
  - `large` (1.5B params): Very slow, best accuracy
- **Long Videos**: Automatically chunked (no manual splitting needed)
- **Batch Processing**: Queue multiple uploads for parallel processing

### Scaling

- **Horizontal Scale**: Add more worker containers for higher throughput
- **Concurrent Limit**: Currently `--pool=solo --concurrency=4` (adjust as needed)
- **Database**: PostgreSQL handles concurrent access safely
- **Cache**: Model stays in memory, re-downloads on restart (persists across container restarts via volume)

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY` (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up HTTPS (nginx reverse proxy or cloud provider)
- [ ] Configure email backend for password resets
- [ ] Use strong database password
- [ ] Enable PostgreSQL backups
- [ ] Monitor worker health and logs
- [ ] Set up log aggregation (e.g., CloudWatch, ELK)
- [ ] Configure resource limits in docker-compose

## Troubleshooting

### Common Issues

**Videos stuck in "Processing" status:**
```bash
# Manually requeue stale videos
docker-compose exec -T web python manage.py requeue_stale_transcriptions --minutes=0
```

**Worker not picking up tasks:**
```bash
# Check Celery worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker
```

**Database connection errors:**
```bash
# Check PostgreSQL is healthy
docker-compose exec db pg_isready -U postgres

# View database service logs
docker-compose logs db
```

**Redis connection issues:**
```bash
# Verify Redis is accessible
docker-compose exec redis redis-cli ping
# Should return: PONG
```

**Model download stuck:**
- First run downloads 461MB model (~70 seconds)
- Model is cached in persistent volume `whisper_cache:/cache/whisper`
- Subsequent runs load from cache (~5 seconds)

## Testing

Run unit tests:

```bash
# With Docker
docker-compose exec -T web python manage.py test

# Locally
python manage.py test transcription
```

Test coverage includes:
- ✅ Authorization (IDOR prevention)
- ✅ AJAX status endpoint
- ✅ Chunked transcription merging
- ✅ Task deletion safety
- ✅ Form validation


## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes and add tests if applicable
4. Commit with conventional messages: `git commit -m "feat: description"`
5. Push to your fork: `git push origin feat/amazing-feature`
6. Open a Pull Request against `main` branch

### Development Workflow

```bash
# Create local development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up local .env with SQLite
cp video_transcriber/.env.example video_transcriber/.env
# Edit to use: DB_ENGINE=sqlite, remove CELERY_* vars for testing

# Run migrations
python manage.py migrate

# Run tests
python manage.py test

# Start development servers (in separate terminals)
redis-server
celery -A video_transcriber worker --loglevel=info
python manage.py runserver
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGES_DOCUMENTATION.md](CHANGES_DOCUMENTATION.md) for detailed documentation of all changes, including:
- Infrastructure & containerization improvements
- Security hardening details
- Task reliability enhancements
- Feature additions and rationale
- Migration guide from previous version

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for planned future enhancements.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) — State-of-the-art speech recognition
- [Django](https://www.djangoproject.com/) — Web framework
- [Celery](https://docs.celeryproject.org/) — Async task queue
- [PostgreSQL](https://www.postgresql.org/) — Reliable database
- [Bootstrap](https://getbootstrap.com/) — Responsive CSS framework
- All contributors who have helped build and improve this tool

## Contact & Support

- **GitHub**: [Co-vengers/video_transcriber](https://github.com/Co-vengers/video_transcriber)
- **Issues**: [GitHub Issues](https://github.com/Co-vengers/video_transcriber/issues)
- **Team**: Co-vengers

## Version

- **Current Version**: 2.0.0 (Production-ready)
- **Python**: 3.12+
- **Django**: 5.1.7
- **Release Date**: March 2026
