from django.urls import path
from . import views

app_name = "login"

urlpatterns = [
    path('', views.index, name="home"),
    path('new-user', views.new_user, name="new-user"),
    path('register', views.register, name="register"),
    path('login', views.login, name="login"),
    path('logout', views.logout, name="logout"),
    path('profile', views.profile, name="profile"),
    path('edit', views.edit_profile, name="edit"),
    path('edit-pw', views.edit_password, name="edit-pw"),
]