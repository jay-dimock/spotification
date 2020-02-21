var token = ""
var playerHasNewUri = true;

$(document).ready(function(){
    $('tr').click(function(){
        // var data = $("#regForm").serialize()   // capture all the data in the form in the variable data
        id=$(this).next('input').val()
        console.log("playlist id: " + id)
        
        $.ajax({
            method: "GET",   // we are using a post request here, but this could also be done with a get
            url: "/spotification/playlist/"+ id,
        })
        .done(function(response){
            $('#playlist').html(response);  // manipulate the dom when the response comes back
            $('#uri').val("spotify:playlist:" + id);
            playerHasNewUri = true;
            handlePlayback($(this), false);
        })
        .fail(function(xhr, status, error) {
            $('#playlist').html(failHtml(xhr, status, error))
        });
    })

    $('.player-button').click(function(e) {
        e.preventDefault();
        var action = $(this).prop('name');
        form = $(this).parent();
        handlePlayback(form, action);
    })
})

function handlePlayback(form, action) {
    $('#player-error').html('');
    var data = $(form).serialize();
    data += "&action=" + action;

    //if uri is not new, player will pick up where it left off instead of starting over
    if (action=="play" && !playerHasNewUri) data += "&continue=true" ;

    //console.log("FORM DATA: " + data);
    $.ajax({
        url: 'handle-playback',
        method: 'post',
        data: data
    })
    .done(function() { 
        if (action=="play") playerHasNewUri = false;
    })
    .fail(function(xhr, status, error) {
        //todo:
        // if(xhr.status == 401 && xhr.message=="The access token expired") {
        //not sure if this will ever happen now that play/pause requests happen server side.
        // }

        //403 can happen if player pauses while already paused or plays while already playing. Ignore.
        if(xhr.status == 403) return;
        $('#player-error').html(failHtml(xhr, status, error))
    });
}

function failHtml(xhr, status, error) {
    return '<h4>ERROR</h4>' +
        '<p><b>' + xhr.status + ": " + xhr.statusText + '</b></p>' +
        '<p class="text-break">' + xhr.responseText + '</p>' 
}

function spotifyWebPlaybackSDKReady(my_token) {
    token = my_token;
    const player = new Spotify.Player({
        name: 'Spotification Player',
        getOAuthToken: cb => { cb(token); }        
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => { console.error(message); });
    player.addListener('authentication_error', ({ message }) => { console.error(message); });
    player.addListener('account_error', ({ message }) => { console.error(message); });
    player.addListener('playback_error', ({ message }) => { console.error(message); });

    // Playback status updates
    player.addListener('player_state_changed', state => { 
        console.log(state); 
        if (!state) return;
        var track = state['track_window']['current_track']
        html = 'Now playing:<ul>' +
            '<li>Track: ' + track['name'] + '</li>' 

        var artists = [];       
        for (var i=0; i<track['artists'].length; i++) {
            artists.push(track['artists'][i]['name'])
        }

        html += '<li>Artists: ' + artists.join(', ') + '</li>' +
            '<li>Album: ' + track['album']['name'] + '</li>' +
            '</ul>'
        $('#current-track').html(html)
    });

    // Ready
    player.addListener('ready', ({ device_id }) => {        
        console.log('Ready with Device ID', device_id);
        $('.device-id').val(device_id);
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
    });

    // Connect to the player!
    player.connect();
}