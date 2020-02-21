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
            //$('#uri-to-play').val("spotify:playlist:" + id);
            playerHasNewUri = true;
            pausePlayback(); 
        })
        .fail(function(xhr, status, error) {
            $('#playlist').html(failHtml(xhr, status, error))
        });
    })

    $('#play').click(function(e) {
        e.preventDefault();
        startPlayback(); 
    });

    
    $('#pause').click(function(e) {
        e.preventDefault();
        pausePlayback();        
    });
})

function startPlayback() {
    var device_id=$('#device-id').val();
    $('#player-error').html('')

    data = ""
    if (playerHasNewUri) {
        uri = $('#playlist-uri').val()
        data = '{"context_uri": "' + uri + '"}'
    }

    $.ajax({
        url: "https://api.spotify.com/v1/me/player/play?device_id=" + device_id,
        type: "PUT",
        data: data,
        beforeSend: function(xhr){xhr.setRequestHeader('Authorization', 'Bearer ' + token );},
    })
    .done(function() { 
        console.log("started playback");
        playerHasNewUri = false;
    })
    .fail(function(xhr, status, error) {
        if(xhr.status != 403) { 
            $('#player-error').html(failHtml(xhr, status, error))
        }            
    });
}

function pausePlayback() {
    var device_id=$('#device-id').val();
    $('#player-error').html('')

    $.ajax({
        url: "https://api.spotify.com/v1/me/player/pause?device_id=" + device_id,
        type: "PUT",
        beforeSend: function(xhr){xhr.setRequestHeader('Authorization', 'Bearer ' + token );},
        success: function(data) { 
            console.log(data)
        }
    })
    .done(function() { console.log("paused playback")})
    .fail(function(xhr, status, error) {
        //todo:
        // if(xhr.status == 401 && xhr.message=="The access token expired") {

        // }
        if(xhr.status != 403) { 
            $('#player-error').html(failHtml(xhr, status, error))
        }            
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
        name: 'Web Playback SDK Quick Start Player',
        getOAuthToken: cb => { cb(token); }        
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => { console.error(message); });
    player.addListener('authentication_error', ({ message }) => { console.error(message); });
    player.addListener('account_error', ({ message }) => { console.error(message); });
    player.addListener('playback_error', ({ message }) => { console.error(message); });

    // Playback status updates
    player.addListener('player_state_changed', state => { console.log(state); });

    // Ready
    player.addListener('ready', ({ device_id }) => {        
        console.log('Ready with Device ID', device_id);
        $('#device-id').val(device_id);
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
    });

    // Connect to the player!
    player.connect();
}