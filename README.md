# SoundNote

A simple yet powerful tool for transcribing video and audio files using OpenAI's Whisper model.

## Overview

Video Transcriber is an open-source tool designed to make transcription accessible and efficient. It leverages OpenAI's Whisper, a state-of-the-art speech recognition model, to provide accurate transcriptions of video and audio content in multiple languages.

## Features

- **Multiple File Format Support**: Process common video and audio formats (MP4, MP3, WAV, etc.)
- **Batch Processing**: Transcribe multiple files at once
- **Language Detection**: Automatically detects the language in your media files
- **User-friendly Interface**: Simple command-line interface for easy use
- **Export Options**: Save transcriptions in multiple formats (TXT, SRT, VTT)
- **Progress Tracking**: Monitor transcription progress in real-time

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for audio extraction from video files)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Co-vengers/video_transcriber.git
   cd video_transcriber
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Running the Development Server

Start the Django development server:
```
python manage.py runserver
```

Access the application at http://127.0.0.1:8000/

## Using the Web Interface

- Login/Register: Create an account or log in to your existing account
- Upload Files: Use the upload form to select and upload your video or audio files
- Configure Settings:

 Select output format (TXT, SRT, VTT)
- Choose Whisper model size (tiny, base, small, medium, large)
- Specify language (or select auto-detection)


Process Files: Click the "Transcribe" button to start processing
Download Results: Once processing is complete, download your transcriptions


## Performance Tips

- Using a GPU significantly improves transcription speed
- Larger models (medium, large) provide better accuracy but require more resources
- For long content, consider splitting files for more efficient processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- All contributors who have helped build and improve this tool

## Contact

Co-vengers Team - [GitHub](https://github.com/Co-vengers)

Project Link: [https://github.com/Co-vengers/video_transcriber](https://github.com/Co-vengers/video_transcriber)
