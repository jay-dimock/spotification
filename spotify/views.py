from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from login.models import User
from spotify.models import *
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import oauth2
import spotipy.util as util
from urllib.parse import urlencode

#from django.views.decorators.csrf import csrf_exempt

def index(request):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    user = User.objects.get(id=request.session['user_id'])

    sp = spotipy.Spotify(auth=token)

    #sp.trace = True
    result = sp.current_user_playlists(limit=50)
    playlists = []

    while result:
        for i in range(len(result['items'])):
            p = result['items'][i]
            if p['owner']['id'] == str(user.spotify_id):
                if user.spotify_id==124103193 and p['name'].startswith('Ryan -'): continue
                playlists.append(p)   
        if result['next']:
            result = sp.next(result)  
        else: result = None

    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
        "my_playlists" : playlists,
        "groups": PlaylistGroup.objects.all,
        "token" : token,
    }
    return render(request, "spotify/index.html", context)  

def playlist(request, id):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    sp = spotipy.Spotify(auth=token)
    p = sp.playlist(playlist_id=id)
    context = {
        "playlist": p,
        "token" : token,
    }
    return render(request, "spotify/partials/playlist.html", context)

def handle_playback(request):
    token = get_token(request.session)
    if not token: 
        raise ValueError('Spotification was unable to retrieve user token') 

    sp = spotipy.Spotify(auth=token)

    action = request.POST['action'].lower()
    device_id=request.POST['device-id']
    uri = request.POST['uri']
    if not uri: #this would happen if user clicked a player button before selecting a playlist.
        return HttpResponse(False)
    #print("POST data:", request.POST)

    if action == "play":
        # by not providing a uri to the api, playback will continue where it left off
        if 'continue' in request.POST: uri = None
        sp.start_playback(device_id=device_id, context_uri=uri)  

    elif action == "skip":
        sp.next_track(device_id=device_id)

    elif action == "pause":
        sp.pause_playback(device_id=device_id)

    else:
        raise ValueError('Spotification: action "' + action + '" not recognized') 

    return HttpResponse(True)

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

def get_scope():
    return 'user-library-read playlist-read-private streaming user-read-email user-read-private'

def token(request):
    #sole purpose here is to provide the UI player with a token so it will not expire after an hour.
    return HttpResponse(get_token(request.session))

def get_token(session):
    if not 'user_id' in session: return None
    email = User.objects.get(id=session['user_id']).email
    oauth = get_oauth(email)
    token_info = oauth.get_cached_token() #Spotipy will auto-refresh if expired
    if not token_info: return None
    return token_info['access_token']

def get_oauth(username):
    oauth = oauth2.SpotifyOAuth(
        client_id = '583e191f6dc9453692417311ed7ed5e0', 
        client_secret='2bb74912877749aebb340f7565e622a3', 
        redirect_uri='http://localhost:8000/spotification/auth',
        scope=get_scope(), 
        username=username)
    return oauth

def no_token_redirect(session):
    if not 'user_id' in session:
        return redirect("login:home")
    else: #under normal circumstances this code block will only be hit one time: immediately after the user registers on the site.
        email = User.objects.get(id=session['user_id']).email

        auth_url = "https://accounts.spotify.com/authorize"
        client_id = '583e191f6dc9453692417311ed7ed5e0'
        scope = get_scope()
        redirect_uri = 'http://localhost:8000/spotification/auth'
        show_dialog = 'false'

        #for demo & debugging purposes, force user to re-approve each time this code block is hit.
        #todo: before deployment, set debug to False.
        debug = True
        if debug: show_dialog = 'true' 

        params = urlencode({
                'client_id': client_id,
                'scope': scope,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'username' : email,
                "show_dialog" : show_dialog
        })
        url = auth_url + '?' + params

        return redirect(auth_url)




