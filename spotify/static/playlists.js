var token = ""
var playerHasNewTracklist = true;

$(document).ready(function(){
    $('#play-playlist-button').hide()
    $('#play-group-button').hide()
    $('#player').hide()

    $('tr').click(function(e){
        if(e.target.getAttribute('modal')=='clone'){
            return;
        }
        id=$(this).next('input').val()
        $(location).attr('href', id);
    });

    $('#new-group-form').submit(function() {
        console.log("new group form hit")
        //only submit form if new group is not whitespace.
        return $.trim($('#new-group').val())
    });

    $('.player-button').click(function(e) {
        e.preventDefault();
        var action = $(this).prop('name');
        handlePlayback(action);
    });

    $('#player-playlist-form').submit(function(e) {
        e.preventDefault();
        var spotify_id = $('#playlist-spotify-id').val();
        //console.log("spotify_id: " + spotify_id);
        //set player uri to match selected playlist
        $('#uri').val('spotify:playlist:' + spotify_id);
        $('#tracklist-type').val('playlist');
        playerHasNewTracklist = true;
        handlePlayback("play");
    })

    $('#player-group-form').submit(function(e) {
        e.preventDefault();
        var group_id = $('#selected-group-id').val();
        if (!group_id || group_id == "0") {
            console.log("No group selected");
            return;
        }
        //set player uri to match selected group
        $('#player-group-id').val(group_id);
        $('#tracklist-type').val('group');
        playerHasNewTracklist = true;
        handlePlayback("play");
    })
})

function handlePlayback(action) {
    $('#player').show();
    $('#player-error').html('');
    var data = $('#player-form').serialize();
    data += "&action=" + action;

    //if uri is not new, player will pick up where it left off instead of starting over
    if (action=="play" && !playerHasNewTracklist) {
        data += "&continue=true";
        console.log("Requesting to continue playback...");
    } else {
        console.log("Requesting to play new tracklist");
    }

    console.log("FORM DATA: " + data);
    $.ajax({
        url: 'handle-playback',
        method: 'post',
        data: data
    })
    .done(function() { 
        if (action=="play") playerHasNewTracklist = false;        
    })
    .fail(function(xhr, status, error) {
        $('#player-error').html(failHtml(xhr, status, error));
    });
}

function failHtml(xhr, status, error) {
    var html = '<h4>ERROR</h4>';
    if (!xhr.status) {
        html += "<p>Unknown error. The server might be offline. Try refreshing the page.</p>"
    } else if (xhr.responseText.startsWith('SpotifyException')) {
        console.log(xhr);
        return "";
    } else {
        html += '<p><b>' + xhr.status + ": " + xhr.statusText + '</b></p>' +
            '<p class="text-break">' + xhr.responseText + '</p>';
    }
    return html;
}

function refreshToken() {
    $.ajax({
        method: "GET", 
        url: "token"
    })
    .done(function(response){
        token = response; //token is a global variable in this script
        console.log("token refreshed")
    })
    .fail(function(xhr, status, error) {
        $('#playlist').html(failHtml(xhr, status, error))
    });
    return token;
}

function spotifyWebPlaybackSDKReady() {
    //token = my_token;
    const player = new Spotify.Player({
        name: 'Spotification Player',
        getOAuthToken: cb => { cb(refreshToken()); }        
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => { console.error('initialization_error', message); });
    
    player.addListener('authentication_error', ({ message }) => { 
        //todo: see if can redirect to somewhere to get new auth token, or something....
        console.error('authentication_error', message); 
    });
    player.addListener('account_error', ({ message }) => { console.error('account_error', message); });
    player.addListener('playback_error', ({ message }) => { console.error('playback_error', message); });

    // Playback status updates
    player.addListener('player_state_changed', state => { 
        console.log(state); 
        if (!state) return;

        var playlist = state['context']['metadata']['context_description']
        var track = state['track_window']['current_track']
        var html = "<ul>"

        if (playlist === undefined) {
            html += '<li>Group: ' + $('#selected-group-id option:selected').text() + '</li>'            
        } else {            
            html += '<li>Playlist: ' + playlist + '</li>'
        }
        
        html += '<li>Track: ' + track['name'] + '</li>' 

        var artists = [];       
        for (var i=0; i<track['artists'].length; i++) {
            artists.push(track['artists'][i]['name'])
        }

        html += '<li>Artists: ' + artists.join(', ') + '</li>' +
            '<li>Album: ' + track['album']['name'] + '</li>' +
            '</ul>'
        $('#current-track').html(html);
    });

    // Ready
    player.addListener('ready', ({ device_id }) => {        
        console.log('Ready with Device ID', device_id);
        $('.device-id').val(device_id);
        $('#play-playlist-button').show();
        $('#play-group-button').show();
        $('#player-error').html('');
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
        var message="<p class='text-danger'>Player hahs gone offline</p>";
        $('#player-error').html(message);
    });

    // Connect to the player!
    player.connect();
}