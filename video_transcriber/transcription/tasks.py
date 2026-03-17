import logging

from celery import shared_task

from .models import Video
from .utils import transcribe_video

logger = logging.getLogger('transcription')

@shared_task(
    bind=True,
    time_limit=3600,
    soft_time_limit=3300,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_transcription(self, video_id, model_size='small'):
    logger.info("Task %s picked for video %s", self.request.id, video_id)
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        logger.error("Video %s not found, skipping transcription.", video_id)
        return

    updated = Video.objects.filter(id=video_id).update(status='processing')
    if not updated:
        logger.warning("Video %s was deleted before processing started.", video_id)
        return

    logger.info("Started transcription for video %s using model '%s'", video_id, model_size)
    try:
        logger.info("Running Whisper transcription for video %s", video_id)
        transcript, segments = transcribe_video(video.file.path, model_size)
        updated = Video.objects.filter(id=video_id).update(
            status='completed',
            transcript=transcript,
            segments=segments,
        )
        if not updated:
            logger.warning("Video %s was deleted before transcription results could be saved.", video_id)
            return
        logger.info("Completed transcription for video %s (segments=%s)", video_id, len(segments or []))
    except Exception as e:
        logger.exception("Transcription failed for video %s: %s", video_id, e)
        updated = Video.objects.filter(id=video_id).update(status='failed')
        if not updated:
            logger.warning("Video %s was deleted after transcription failure; skipping status update.", video_id)
