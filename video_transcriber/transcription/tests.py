from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Video
from .tasks import process_transcription
from .utils import transcribe_video


class VideoAuthorizationTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username='owner', password='pass12345')
		self.other_user = User.objects.create_user(username='other', password='pass12345')
		self.video = Video.objects.create(
			user=self.owner,
			title='Owner Video',
			file='videos/test.mp4',
			status='pending',
		)

	def test_video_detail_for_non_owner_returns_404(self):
		self.client.force_login(self.other_user)
		response = self.client.get(reverse('video_detail', args=[self.video.id]))
		self.assertEqual(response.status_code, 404)


class VideoStatusEndpointTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='alice', password='pass12345')
		self.other_user = User.objects.create_user(username='bob', password='pass12345')

	def test_video_status_requires_login(self):
		video = Video.objects.create(
			user=self.user,
			title='Sample',
			file='videos/test.mp4',
			status='processing',
		)
		response = self.client.get(reverse('video_status', args=[video.id]))
		self.assertEqual(response.status_code, 302)

	def test_video_status_returns_json_for_owner(self):
		video = Video.objects.create(
			user=self.user,
			title='Sample',
			file='videos/test.mp4',
			status='processing',
		)
		self.client.force_login(self.user)

		response = self.client.get(reverse('video_status', args=[video.id]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['status'], 'processing')
		self.assertFalse(response.json()['is_done'])

	def test_video_status_returns_done_for_completed_video(self):
		video = Video.objects.create(
			user=self.user,
			title='Done',
			file='videos/test.mp4',
			status='completed',
		)
		self.client.force_login(self.user)

		response = self.client.get(reverse('video_status', args=[video.id]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['status'], 'completed')
		self.assertTrue(response.json()['is_done'])

	def test_video_status_for_non_owner_returns_404(self):
		video = Video.objects.create(
			user=self.user,
			title='Private',
			file='videos/test.mp4',
			status='processing',
		)
		self.client.force_login(self.other_user)

		response = self.client.get(reverse('video_status', args=[video.id]))

		self.assertEqual(response.status_code, 404)


class TranscriptionChunkMergeTests(TestCase):
	@patch('transcription.utils._extract_chunk_audio')
	@patch('transcription.utils._probe_duration_seconds')
	@patch('transcription.utils.get_model')
	def test_chunked_transcription_is_merged_into_one_output(self, mock_get_model, mock_probe_duration, mock_extract_chunk_audio):
		class FakeModel:
			def __init__(self):
				self.calls = 0

			def transcribe(self, _, **kwargs):
				responses = [
					{
						'text': 'hello from chunk one',
						'segments': [
							{'start': 0.0, 'end': 2.0, 'text': 'hello'},
						],
					},
					{
						'text': 'and chunk two',
						'segments': [
							{'start': 0.5, 'end': 3.0, 'text': 'world'},
						],
					},
					{
						'text': 'last chunk',
						'segments': [
							{'start': 1.0, 'end': 2.0, 'text': '!'},
						],
					},
				]
				response = responses[self.calls]
				self.calls += 1
				return response

		mock_get_model.return_value = FakeModel()
		mock_probe_duration.return_value = 1250.0

		transcript, segments = transcribe_video(
			'dummy.mp4',
			model_name='small',
			chunk_seconds=600,
			chunk_threshold_seconds=900,
		)

		self.assertEqual(transcript, 'hello from chunk one and chunk two last chunk')
		self.assertEqual(len(segments), 3)
		self.assertEqual(segments[0]['start'], 0.0)
		self.assertEqual(segments[1]['start'], 600.5)
		self.assertEqual(segments[2]['start'], 1201.0)
		self.assertEqual(mock_extract_chunk_audio.call_count, 3)

	@patch('transcription.utils._probe_duration_seconds')
	@patch('transcription.utils.get_model')
	def test_short_media_uses_single_pass_transcription(self, mock_get_model, mock_probe_duration):
		class FakeModel:
			def transcribe(self, _, **kwargs):
				return {
					'text': 'single pass',
					'segments': [
						{'start': 0.0, 'end': 1.0, 'text': 'single'},
					],
				}

		mock_get_model.return_value = FakeModel()
		mock_probe_duration.return_value = 120.0

		transcript, segments = transcribe_video('short.mp4', chunk_threshold_seconds=900)

		self.assertEqual(transcript, 'single pass')
		self.assertEqual(len(segments), 1)
		self.assertEqual(segments[0]['text'], 'single')


class TranscriptionTaskSafetyTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='task-user', password='pass12345')

	@patch('transcription.tasks.transcribe_video')
	def test_deleted_video_during_processing_does_not_crash_task(self, mock_transcribe_video):
		video = Video.objects.create(
			user=self.user,
			title='Transient',
			file='videos/test.mp4',
			status='pending',
		)

		def delete_then_return(*args, **kwargs):
			Video.objects.filter(id=video.id).delete()
			return 'done', [{'start': 0.0, 'end': 1.0, 'text': 'done'}]

		mock_transcribe_video.side_effect = delete_then_return

		process_transcription.run(video.id, 'small')

		self.assertFalse(Video.objects.filter(id=video.id).exists())
