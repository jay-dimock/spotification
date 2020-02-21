from django.shortcuts import render, redirect, HttpResponse
from login.models import User
from spotify.models import *
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

def play(request):
    token = get_token(request.session)
    if not token: return HttpResponse(False)
    #example player id: 36353f8f066ee033eaba11e4600083677ddd77d2

    sp = spotipy.Spotify(auth=token)
    #sp.start_playback(device_id=device_id, uris=my_tracks)
    print("*"*60)
    print("device-id:", request.POST['device-id'])
    print("uri:", request.POST['uri'])
    print("*"*60)

    
    #curl -X "PUT" "https://api.spotify.com/v1/me/player/play?device_id=36353f8f066ee033eaba11e4600083677ddd77d2" 
    # --data "{\"context_uri\":\"spotify:album:5ht7ItJgpBH7W6vJ5BqpPr\",\"offset\":{\"position\":5},\"position_ms\":0}" 
    # -H "Accept: application/json" -H "Content-Type: application/json" 
    # -H "Authorization: Bearer BQAjoORMWDKQ5pGHoSPuU0N81RSQ9gE_Xowjjgbsi4i0sdKAJDPFXVvvMmdQ4S6yv3G6rGl7g4ppEz3PSB7XDHzKl1PBlvNww6fk1rxMn98KP8UuFevwIGOzxccJZ7HuUxj4g4Cr7Tuf7PQxq2pJrHCFCx2Pk_uxgvatThHXMv8HkNVPiMwkA2g"

    # params = urlencode({
    #     'device_id': request.POST['device-id'],
    #     'scope': get_scope(),
    #     'context_uri': request.POST['uri'],
    #     'response_type': 'code',
    #     'username' : username,
    #     "show_dialog" : show_dialog
    # })

    sp.start_playback(
        device_id=request.POST['device-id'], 
        context_uri=request.POST['uri'])
    return HttpResponse(True)


def pause(request):
    token = get_token(request.session)
    if not token: return HttpResponse(False)

    device_id = request.POST['device_id']
    sp = spotipy.Spotify(auth=token)
    sp.pause_playback(device_id=device_id)
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

def get_auth_url(username):
    auth_url = "https://accounts.spotify.com/authorize"
    client_id = '583e191f6dc9453692417311ed7ed5e0'
    #client_secret = '2bb74912877749aebb340f7565e622a3'
    scope = get_scope()
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
        scope=get_scope(), 
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
        return redirect(get_auth_url(email))




