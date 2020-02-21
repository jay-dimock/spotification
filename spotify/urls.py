from django.urls import path
from . import views

app_name = "spotification"

urlpatterns = [
    path('', views.index, name="home"),	  
    path('auth', views.auth, name="auth"), 
    path('playlist/<id>', views.playlist, name="playlist"),
    path('play', views.play, name="play"),
    path('pause', views.pause, name="pause"),
    path('handle-playback', views.handle_playback, name="handle-playback")
]