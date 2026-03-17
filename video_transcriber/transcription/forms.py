import os
from django import forms
from .models import Video

class VideoUploadForm(forms.ModelForm):
    ALLOWED_VIDEO_TYPES = [
    'video/mp4', 'video/mpeg', 'video/quicktime',
    'video/x-msvideo', 'video/webm', 'video/ogg',
    'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac',
    ]
    ALLOWED_EXTENSIONS = [
        '.mp4', '.mpeg', '.mpg', '.mov', '.avi', '.webm', '.ogg',
        '.mp3', '.wav', '.flac',
    ]
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

    MODEL_CHOICES = [
        ('tiny', 'Tiny (fastest, least accurate)'),
        ('base', 'Base'),
        ('small', 'Small (default)'),
        ('medium', 'Medium'),
        ('large', 'Large (slowest, most accurate)'),
    ]
    model_size = forms.ChoiceField(
        choices=MODEL_CHOICES,
        initial='small',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError('Unsupported file type. Please upload a video or audio file.')
            if file.content_type not in self.ALLOWED_VIDEO_TYPES:
                raise forms.ValidationError('Unsupported file type. Please upload a video or audio file.')
            if file.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError('File too large. Maximum size is 500 MB.')
        return file

    class Meta:
        model = Video
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
