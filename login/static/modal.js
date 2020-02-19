$(document).ready(function(){
    
    var mm=$("#modal-message").html().trim();
    //console.log("mm: " + mm);
    if (mm) {
        $("#myModal").css("display", "block")

        window.onclick = function() {
            $("#myModal").css("display", "none")
        }
    }
});

