from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from transcription.models import Video
from transcription.tasks import process_transcription


class Command(BaseCommand):
    help = "Requeue stale videos stuck in processing state."

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=45,
            help='Treat processing records older than this many minutes as stale.',
        )
        parser.add_argument(
            '--model-size',
            type=str,
            default='small',
            help='Model size to use when requeueing stale jobs.',
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        model_size = options['model_size']
        cutoff = timezone.now() - timedelta(minutes=minutes)

        stale_videos = Video.objects.filter(
            status__in=['processing', 'pending'],
            uploaded_at__lt=cutoff,
            transcript__isnull=True,
        )

        count = stale_videos.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No stale processing videos found.'))
            return

        for video in stale_videos:
            if video.status != 'pending':
                video.status = 'pending'
                video.save(update_fields=['status'])
            process_transcription.delay(video.id, model_size)

        self.stdout.write(
            self.style.SUCCESS(
                f'Requeued {count} stale processing video(s) using model size "{model_size}".'
            )
        )
