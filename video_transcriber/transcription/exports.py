def format_srt_time(seconds):
    """Convert seconds (float) to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_txt(video):
    """Return plain text transcript."""
    if video.transcript:
        return video.transcript
    return ""


def export_srt(video):
    """Return transcript in SRT subtitle format using segment timestamps."""
    if not video.segments:
        # Fall back to plain text with no timestamps
        return video.transcript or ""

    lines = []
    for i, seg in enumerate(video.segments, start=1):
        start = format_srt_time(seg['start'])
        end = format_srt_time(seg['end'])
        text = seg['text'].strip()
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")  # blank line separator

    return "\n".join(lines)
