from django.db import models
from login.models import User

class PlaylistGroup(models.Model):
    user = models.ForeignKey(User, related_name="playlist_groups", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Playlist(models.Model):
    playlist_group = models.ForeignKey(User, related_name="playlists", on_delete=models.CASCADE)
    playlist_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['playlist_group', 'playlist_id'], name="unique_constraint_group_playlist")
        ]
