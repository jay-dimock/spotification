$(document).ready(function(){
    if(jQuery('#myModal').length) {
        var mm=$("#modal-message").html().trim();
        if (mm) {
            $("#myModal").css("display", "block")

            window.onclick = function() {
                $("#myModal").css("display", "none")
            }
        }
    }

    $('.close-modal').click(function() {
        $('.modal').css("display", "none");        
    });

    $('#delete-group-link').click(function() {
        $('#delete-modal').css("display", "block");
    });

    $('.clone-link').click(function() {
        $('.clone-modal').css("display", "block");
    });

    $('#rename-group-link').click(function() {
        $('#rename-modal').css("display", "block");
    })
    
});