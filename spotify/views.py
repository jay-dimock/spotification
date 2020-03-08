from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from login.models import User
from spotify.models import *
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import oauth2
import spotipy.util as util
import urllib
from urllib.error import HTTPError
from urllib.parse import urlencode
import random
from django.conf import settings
import json
import math


#from django.views.decorators.csrf import csrf_exempt

def index(request):
    if not 'user_id' in request.session:
        return redirect("login:home")

    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
    }
    return render(request, "spotify/index.html", context)  


def playlists_start(request):
    spotify_id = None
    if 'playlist_spotify_id' in request.session:
        spotify_id = request.session['playlist_spotify_id']
    return redirect("spotification:playlists", spotify_id=spotify_id)


def playlists(request, spotify_id):    
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    request.session['playlist_spotify_id'] = spotify_id

    user = User.objects.get(id=request.session['user_id'])
    
    api_result = get_all_playlists(user, token, spotify_id)
    
    playlist_groups = []
    available_groups = []
    internal_playlist_id = 0;

    existing = Playlist.objects.filter(spotify_id=spotify_id, user=user)

    if existing.count() > 0:
        pl = existing.first()
        internal_playlist_id = pl.id
        playlist_groups = pl.groups.all()

        for pg in user.playlist_groups.all().order_by('name'):
            if not playlist_groups.filter(id=pg.id).exists():
                available_groups.append(pg)
    else:
        available_groups = user.playlist_groups.all().order_by('name')

    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
        "user_spotify_id" : User.objects.get(id = request.session['user_id']).spotify_id,
        "my_playlists" : api_result['playlists'],
        "selected_playlist" : api_result['selected_playlist'],
        "internal_playlist_id": internal_playlist_id,
        "playlist_groups": playlist_groups,
        "available_groups": available_groups 
    }
    return render(request, "spotify/playlists.html", context)  


def get_all_playlists(user, token, spotify_playlist_id=None):
    sp = spotipy.Spotify(auth=token)

    result = sp.current_user_playlists(limit=50)
    playlists = []
    selected_playlist = None

    while result:
        for i in range(len(result['items'])):
            p = result['items'][i]
            # if p['owner']['id'] == str(user.spotify_id): #for the moment, only show playlists owned by this user
                #for Jay D's account only: filter out friend Ryan's playlists:
            if user.spotify_id=="124103193" and p['name'].startswith('Ryan -'): continue
            playlists.append(p)  
            if p['id'] == spotify_playlist_id:
                selected_playlist = p
        if result['next']:
            result = sp.next(result)  
        else: result = None

    playlists = sorted(playlists, key=lambda playlist: playlist['name'])

    return {"playlists": playlists, "selected_playlist":selected_playlist}


def groups_start(request):
    group_id = 0
    if 'group_id' in request.session:
        group_id = request.session['group_id']
    return redirect("spotification:groups", group_id=group_id)


def groups(request, group_id):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)
    
    user = User.objects.get(id=request.session['user_id'])
    selected_group = get_selected_group(request.session, group_id)

    playlists=[]
    if selected_group:
        sp = spotipy.Spotify(auth=token)
        for p in selected_group.playlists.all():
            #debug_print(p.spotify_id)
            try:
                result = sp.playlist(playlist_id=p.spotify_id, fields="name,id")
                playlists.append({ "id":p.id, "name":result['name']})
            except spotipy.SpotifyException as e: 
                debug_print(e)
            
    api_result = get_all_playlists(user, token)    

    context = {
        "user_name" : User.objects.get(id=request.session['user_id']).full_name,
        "groups": user.playlist_groups.all().order_by('name'),
        "selected_group": selected_group,
        "selected_playlists": playlists,
        "all_playlists": api_result['playlists'],
    }
    return render(request, "spotify/groups.html", context)


def get_selected_group(session, group_id=None):
    if group_id: 
        session['group_id'] = group_id
    elif 'group_id' in session:
        group_id = session['group_id']
    else:
        return None

    existing = PlaylistGroup.objects.filter(id=group_id)
    if existing.count() == 0: #if count is 0, this means user has deleted group, so session value is stale.
        del session['group_id']
        return None
    
    return existing.first()


def player(request):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    current_spotify_id = ""
    if 'playlist_spotify_id' in request.session:
        current_spotify_id = request.session['playlist_spotify_id']
    
    user = User.objects.get(id=request.session['user_id'])

    api_result = get_all_playlists(user, token, current_spotify_id)

    current_group = get_selected_group(request.session)
    
    current_playlist_id=""
    if api_result["selected_playlist"]:
        current_playlist_id = api_result["selected_playlist"]["id"]

    context = {
        "user_name" : user.full_name,
        # "token" : token,
        "groups" : user.playlist_groups.all().order_by('name'),
        "playlists" : api_result['playlists'],
        "current_group": current_group,
        "current_spotify_id": current_playlist_id,
    }
    return render(request, "spotify/player.html", context)  


def update_playlist(request):
    if not 'user_id' in request.session:
        return redirect("login:home")

    #debug_print(request.POST)

    user = User.objects.get(id=request.session['user_id'])
    group_id = int(request.POST['group-id'])

    new_group_id = add_group(user, request.POST['new-group'])
    if new_group_id > 0: group_id = new_group_id

    spotify_id = request.POST['playlist-id']
    if not spotify_id:
        debug_print("Expected playlist spotify ID in POST data but got empty string")
        return redirect("spotification:playlists-start")    

    if group_id > 0:
        add_playlist_to_group(user.id, spotify_id, group_id)   

    return redirect("spotification:playlists", spotify_id=spotify_id)

def new_group(request):
    if not 'user_id' in request.session:
        return redirect("login:home")
    user = User.objects.get(id=request.session['user_id'])
    group_id = add_group(user,request.POST['new-group'])
    return redirect("spotification:groups", group_id=group_id)

#Clone a playlist that the user doesn't own, add it to the database, and unfollow the original playlist
def clone_followed_playlist(request):
    token = get_token(request.session)
    if not token: return no_token_redirect(request.session)

    sp = spotipy.Spotify(auth=token)
    current_user = User.objects.get(id = request.session['user_id'])
    list_of_track_uris = []
    new_playlist = sp.user_playlist_create(current_user.spotify_id, request.POST['playlist_name'], public=False, description='')
    offset = 0
    original_playlist_tracks_dict = sp.playlist_tracks(request.POST['playlist_id'], fields='total, items(track(uri)), items(is_local)', limit=100, offset=offset, market=None)
    #Can only add 100 songs to a playlist at a time. This loop grabs 100 at a time from the og playlist, adds it to the new playlist, and moves the offset by 100 to grab the next portion of songs
    while offset < original_playlist_tracks_dict['total']:
        for key in original_playlist_tracks_dict['items']:
            if not bool(key['is_local']): #unable to add local tracks to a playlist
                list_of_track_uris.append(key['track']['uri'])
            else:
                print("*** skipping local track:", key['track']['uri'], "***")  

        #This covers the case where all 100 tracks being scanned are local tracks and would break not adding tracks to the playlist
        if len(list_of_track_uris) > 0:
            sp.user_playlist_add_tracks(current_user.id, new_playlist['id'], list_of_track_uris)
        list_of_track_uris = []
        offset += 100
        original_playlist_tracks_dict = sp.playlist_tracks(request.POST['playlist_id'], fields='total, items(track(uri)), items(is_local)', limit=100, offset=offset, market=None)
    unfollowed = sp.user_playlist_unfollow(current_user.spotify_id, request.POST['playlist_id'])
    return redirect('spotification:playlists-start')

# given a group name: if group exists, returns group id, else creates group & returns new group id.
def add_group(user, group_name):
    name = group_name.strip()
    if not group_name: return 0
    existing = PlaylistGroup.objects.filter(user=user, name=name)
    if existing.count() > 0: return existing.first().id
    return PlaylistGroup.objects.create(user=user, name=name).id


def update_group(request):
    group_id = int(request.POST['group-id'])
    spotify_id = request.POST['spotify-id']
    if not spotify_id: #user probably clicked Add without choosing a playlist
        return redirect("spotification:groups", group_id=group_id)

    if not 'user_id' in request.session:
        return redirect("login:home")    

    #debug_print(request.POST)
    add_playlist_to_group(request.session['user_id'], spotify_id, group_id)
    return redirect("spotification:groups", group_id=group_id)


def add_playlist_to_group(user_id, spotify_id, group_id):
    #this gets called from 2 different pages    
    group = PlaylistGroup.objects.get(id=group_id)
    playlists = Playlist.objects.filter(spotify_id=spotify_id)
    if playlists.count() == 0:
        user = User.objects.get(id=user_id)        
        Playlist.objects.create(user=user, spotify_id=spotify_id)
    playlist = Playlist.objects.get(spotify_id=spotify_id)
    playlist.groups.add(group)


def degroup(request, group_id, internal_playlist_id, page):
    group = PlaylistGroup.objects.get(id=group_id)
    playlist = Playlist.objects.get(id=internal_playlist_id)
    group.playlists.remove(playlist)
    if page == 'playlists':
        return redirect("spotification:playlists", spotify_id=playlist.spotify_id)
    else:
        return redirect("spotification:groups", group_id=group.id)

def delete_group(request):
    if not 'user_id' in request.session:
        return redirect("login:home")

    user = User.objects.get(id=request.session["user_id"])
    group = PlaylistGroup.objects.get(id=request.POST["group-id"])
    if group.user == user:
        group.delete()
    return redirect("spotification:groups-start")

def rename_group(request):
    if not 'user_id' in request.session:
        return redirect("login:home")
    new_name=request.POST["new-name"].strip()
    if new_name:
        group = PlaylistGroup.objects.get(id=request.POST["group-id"])
        group.name = new_name
        group.save()
    return redirect("spotification:groups", group_id=request.POST["group-id"])


def handle_playback(request):
    if not valid_playback_request(request.POST):
        return HttpResponse(False)

    token = get_token(request.session)
    if not token: 
        #raise HTTPError('handle_playback', 401, 'Spotification was unable to retrieve user token')
        raise PermissionDenied
        #raise ValueError('Spotification was unable to retrieve user token') 

    sp = spotipy.Spotify(auth=token)

    action = request.POST['action'].lower()
    device_id = request.POST['device-id']

    # print("*"*50, "\nPOST data:", request.POST)

    if action == "play":
        # by not providing a uri to the api, playback will continue where it left off
        if 'continue' in request.POST: 
            sp.start_playback(device_id=device_id) 
        else:
            tracklist_type = request.POST['tracklist-type']
            if tracklist_type == 'playlist':
                sp.start_playback(device_id=device_id, context_uri=request.POST['uri']) 
            elif tracklist_type == 'group':
                tracks = get_tracks_for_group(request.POST['group-id'], token)
                if len(tracks) == 0: 
                    return HttpResponse(False)
                try:
                    sp.start_playback(device_id=device_id, uris=tracks)
                except spotipy.SpotifyException as e: 
                    debug_print(e)

    elif action == "skip":
        sp.next_track(device_id=device_id)

    elif action == "pause":
        sp.pause_playback(device_id=device_id)

    else:
        raise ValueError('Spotification: action "' + action + '" not recognized') 

    return HttpResponse(True)

def get_tracks_for_group(group_id, token):
    groups = PlaylistGroup.objects.filter(id=group_id)
    if groups.count() == 0:
        debug_print("PlaylistGroup " + group_id + " not found in database")
        return []
    group = groups.first()
    tracks = []    

    sp = spotipy.Spotify(auth=token)
    for playlist in group.playlists.all():
        offset = 0
        while True:
            response = sp.playlist_tracks(
                playlist_id=playlist.spotify_id
                , fields="items.track.uri, items.is_local"
                , offset=offset)
            
            if len(response['items']) == 0:
                break

            for item in response['items']:
                if not bool(item['is_local']): #player won't play "local" (non-spotify) tracks
                    tracks.append(item['track']['uri'])
                else:
                    print("*** skipping local track:", item['track']['uri'], "***")

            offset += len(response['items'])

    tracks=list(set(tracks)) #this removes duplicate tracks
    random.shuffle(tracks)

    message = "tracks retrieved: " + str(len(tracks))

    #JD: If there are too many tracks, Spotify throws this error:
    #HTTPError: 413 Client Error: Request Entity Too Large for url
    #Their documentation doesn't say what the limit is, but testing revealed that 800 tracks threw the error
    #while 780 tracks did not. To be safe, setting limit to 750 tracks.
    max_tracks = 750
    if len(tracks) > max_tracks:        
        del tracks[max_tracks:] #delete all elements after the max
        message += "\ntruncated to " + str(len(tracks)) + " tracks"
    # debug_print(message)
    return tracks;


def valid_playback_request(post):
    device_id = post['device-id']
    if not device_id: 
        debug_print("No device id provided")
        return False

    tracklist_type = post['tracklist-type']
    if not tracklist_type:
        debug_print("No tracklist type provided")
        return False   
    

    if tracklist_type == "playlist":
        if not post['uri']:
            debug_print("No playlist uri provided")
            return False

    elif tracklist_type == "group":
        group_id = post['group-id']
        if not group_id or group_id == "0":
            debug_print("No group id provided")
            return False

    else:
        debug_print("Tracklist type '" + tracklist_type + "' not recognized")
        return False

    return True  


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
    
    if 'code' not in request.GET:
        message = ''
        if 'error' in request.GET:
            e = request.GET['error']
            if e == 'access_denied':
                message = "<p>Spotify access was denied. In order to use this site, you will need to approve for Spotify to have the "\
                "requested access. Spotification will only use this access when you are logged in and actively using the site "\
                "for what is was designed for.</p>"\
                "<p>Use the BACK button in your browser to go back and approve.</p>"
            else: 
                message = "Spotify authorization response returned this error code: <b>" + e + "</b>"
        else:
            message="Cannot authorize Spotify. No auth code was provided in the auth result."
        return error(request, message)

    user = User.objects.get(id=request.session['user_id'])

    sp_oauth = get_oauth(user.email) 
    token_info = sp_oauth.get_access_token(code = request.GET['code'], as_dict=True)

    if not token_info:
        return error(request, "Auth code was sent to Spotify but no token info was returned")

    if not user.spotify_id:
        sp = spotipy.Spotify(token_info['access_token'])
        results = sp.current_user()
        user.spotify_id = results['id']
        user.save()
    
    return redirect('spotification:home')


def token(request):
    #sole purpose here is to provide the UI player with a token so it will not expire after an hour.
    return HttpResponse(get_token(request.session))


def get_token(session):
    if not 'user_id' in session: return None
    email = User.objects.get(id=session['user_id']).email
    oauth = get_oauth(email)
    token_info = oauth.get_cached_token()#Spotipy will auto-refresh if expired
    if not token_info: return None
    return token_info['access_token']


def no_token_redirect(session):
    #get_token was unable to retrieve cached token. we need to send the user to the appropriate place (to either log in to our app or approve spotify access).
    if not 'user_id' in session:
        return redirect("login:home")
    else: #under normal circumstances this code block will only be hit one time: immediately after the user registers on the site.
        email = User.objects.get(id=session['user_id']).email
        sp_oauth = get_oauth(email) 
        #sends a request to spotify asking for an auth code.
        #spotify will recirect to the URL we provided in the oauth object (in this case, our auth endpoint)
        #our auth endpoint parses out the auth code and exchanges it for a token (see auth method above)
        return redirect(sp_oauth.get_authorize_url())


def get_oauth(username):
    #scope is the list of spotify permissions the user will need to approve
    scope = 'user-library-read playlist-read-private streaming user-read-email user-read-private playlist-modify-private playlist-modify-public'

    oauth = oauth2.SpotifyOAuth(
        client_id = settings.SPOTIFY_CLIENT_ID, 
        client_secret= settings.SPOTIFY_CLIENT_SECRET, 
        redirect_uri='http://localhost:8000/spotification/auth',
        scope=scope, 
        username=username,
        show_dialog=True)
    return oauth


def debug_print(thing_to_print):
    print("*"*50, "\n", thing_to_print, "\n", "*"*50)