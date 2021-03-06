from django.urls import path
from . import views

app_name = "spotification"

urlpatterns = [
    path('', views.index, name="home"),	  
    path('auth', views.auth, name="auth"), 
    path('handle-playback', views.handle_playback, name="handle-playback"),
    path('token', views.token, name="token"),
    path('update-playlist', views.update_playlist, name="update-playlist"),
    path('update-group', views.update_group, name="update-group"),
    path('degroup/<int:group_id>/<int:internal_playlist_id><page>', views.degroup, name="degroup"),
    path('playlists-start', views.playlists_start, name="playlists-start"),
    path('playlists/<spotify_id>', views.playlists, name="playlists"),
    path('groups-start', views.groups_start, name="groups-start"),
    path('groups/<int:group_id>', views.groups, name="groups"),
    path('new-group', views.new_group, name="new-group"),
    path('rename-group', views.rename_group, name="rename-group"),
    path('delete-group', views.delete_group, name="delete-group"),
    path('player', views.player, name="player"),
    path('clone_playlist', views.clone_followed_playlist, name="clone_playlist"),
]