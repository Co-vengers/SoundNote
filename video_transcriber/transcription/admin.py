from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('transcript', 'uploaded_at')
