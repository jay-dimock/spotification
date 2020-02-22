from django.urls import path
from . import views

app_name = "spotification"

urlpatterns = [
    path('', views.index, name="home"),	  
    path('auth', views.auth, name="auth"), 
    path('playlist/<id>', views.playlist, name="playlist"),
    path('handle-playback', views.handle_playback, name="handle-playback"),
    path('token', views.token, name="token"),
    path('update-playlist', views.update_playlist, name="update-playlist"),
    path('degroup/<int:group_id>/<int:internal_playlist_id>', views.degroup, name="degroup"),
]