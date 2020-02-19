from django.shortcuts import render, redirect
from login.models import User
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import oauth2
import spotipy.util as util
from urllib.parse import urlencode



def index(request):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    user = User.objects.get(id=request.session['user_id'])

    sp = spotipy.Spotify(auth=token)

    #sp.trace = True
    result = sp.current_user_playlists(limit=50)

    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
        "my_playlists" : result['items'],
    }
    return render(request, "spotify/index.html", context)  

def error(request, error_message):
    if not 'user_id' in request.session:
        return redirect("login:home")
    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
        "error" : error_message
    }
    return render(request, "spotify/error.html", context)

def auth(request):
    if not 'user_id' in request.session:
        return redirect("login:home")    
    
    message = ''
    if 'code' not in request.GET:
        if 'error' in request.GET:
            message = "Spotify authorization response returned this error code: <b>" + request.GET['error'] + "</b>"
        else:
            message="Cannot authorize Spotify. No auth code was provided in the auth result."
        return error(request, message)

    user = User.objects.get(id=request.session['user_id'])

    sp_oauth = get_oauth(user.email) 
    token_info = sp_oauth.get_access_token(code = request.GET['code'])

    if not token_info:
        return error(request, "Auth code was sent to Spotify but no token info was returned")

    user.token = token_info['access_token']
    user.refresh_token = token_info['refresh_token']

    if not user.spotify_id:
        sp = spotipy.Spotify(auth=user.token)
        results = sp.current_user()
        user.spotify_id = results['id']

    user.save()
    return redirect('spotification:home')

def get_auth_url(username):
    auth_url = "https://accounts.spotify.com/authorize"
    client_id = '583e191f6dc9453692417311ed7ed5e0'
    #client_secret = '2bb74912877749aebb340f7565e622a3'
    scope = 'user-library-read playlist-read-private'
    redirect_uri = 'http://localhost:8000/spotification/auth'
    show_dialog = 'false'
    debug = True
    if debug: show_dialog = 'true'

    params = urlencode({
            'client_id': client_id,
            'scope': scope,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'username' : username,
            "show_dialog" : show_dialog
    })
    url = auth_url + '?' + params
    return url

def get_oauth(username):
    oauth = oauth2.SpotifyOAuth(
        client_id = '583e191f6dc9453692417311ed7ed5e0', 
        client_secret='2bb74912877749aebb340f7565e622a3', 
        redirect_uri='http://localhost:8000/spotification/auth',
        scope='user-library-read playlist-read-private', 
        username=username)
    return oauth

def get_token(session):
    if not 'user_id' in session: return None
    email = User.objects.get(id=session['user_id']).email
    oauth = get_oauth(email)
    token_info = oauth.get_cached_token() #Spotipy will auto-refresh if expired
    if not token_info: return None
    return token_info['access_token']

def no_token_redirect(session):
    if not 'user_id' in session:
        return redirect("login:home")
    else:
        email = User.objects.get(id=session['user_id']).email
        return redirect(get_auth_url(user.email))




