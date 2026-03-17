import math
import subprocess
import tempfile

import whisper

_models = {}


def get_model(model_name="small"):
    if model_name not in _models:
        _models[model_name] = whisper.load_model(model_name)
    return _models[model_name]


def _probe_duration_seconds(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except (TypeError, ValueError):
        return None


def _extract_chunk_audio(video_path, output_audio_path, start_seconds, duration_seconds):
    command = [
        'ffmpeg',
        '-hide_banner',
        '-loglevel', 'error',
        '-ss', str(start_seconds),
        '-i', video_path,
        '-t', str(duration_seconds),
        '-vn',
        '-ac', '1',
        '-ar', '16000',
        '-acodec', 'pcm_s16le',
        output_audio_path,
        '-y',
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        raise RuntimeError(f'ffmpeg chunk extraction failed: {stderr}')


def _offset_segments(raw_segments, offset_seconds):
    adjusted = []
    for segment in raw_segments or []:
        start = float(segment.get('start', 0.0)) + offset_seconds
        end = float(segment.get('end', 0.0)) + offset_seconds
        text = (segment.get('text') or '').strip()
        adjusted.append({'start': start, 'end': end, 'text': text})
    return adjusted


def transcribe_video(video_path, model_name="small", chunk_seconds=600, chunk_threshold_seconds=900):
    model = get_model(model_name)
    duration = _probe_duration_seconds(video_path)

    if duration is None or duration <= chunk_threshold_seconds:
        result = model.transcribe(video_path, fp16=False)
        segments = [
            {'start': s['start'], 'end': s['end'], 'text': s['text']}
            for s in (result.get('segments') or [])
        ]
        return result.get('text') or '', segments

    merged_text_parts = []
    merged_segments = []
    total_chunks = int(math.ceil(duration / float(chunk_seconds)))

    with tempfile.TemporaryDirectory(prefix='vt_chunks_') as temp_dir:
        for chunk_index in range(total_chunks):
            chunk_start = chunk_index * chunk_seconds
            chunk_duration = min(chunk_seconds, duration - chunk_start)
            if chunk_duration <= 0:
                continue

            chunk_audio_path = f"{temp_dir}/chunk_{chunk_index:04d}.wav"
            _extract_chunk_audio(video_path, chunk_audio_path, chunk_start, chunk_duration)

            result = model.transcribe(chunk_audio_path, fp16=False)
            chunk_text = (result.get('text') or '').strip()
            if chunk_text:
                merged_text_parts.append(chunk_text)

            merged_segments.extend(_offset_segments(result.get('segments'), chunk_start))

    merged_text = ' '.join(merged_text_parts).strip()
    return merged_text, merged_segments
