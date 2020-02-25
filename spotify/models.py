from django.db import models
from login.models import User
from django.db.models import Q
from django.db.models import Lookup
from django.db.models.fields import Field

@Field.register_lookup
class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s <> %s' % (lhs, rhs), params


class PlaylistGroup(models.Model):
    user = models.ForeignKey(User, related_name="playlist_groups", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name="unique_constraint_group_name")            
        ]

class Playlist(models.Model):
    user = models.ForeignKey(User, related_name="playlists", on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=255, blank=False)
    groups = models.ManyToManyField(PlaylistGroup, related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['spotify_id', 'user'], name="unique_constraint_playlist_id_user"),
            models.CheckConstraint(check=Q(spotify_id__ne=''), name="spotify_id_not_empty")
        ]