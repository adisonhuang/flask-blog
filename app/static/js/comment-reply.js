//Rest the value when reply-dialog-box dismiss
function undo_reply() {
    $('#follow_id').val(-1);
    $('#follow').val("");
}

$("#content").on('input', function () {
    var contentStr = $("#content").val().replace(/\s+/g, "");
    if (contentStr == "") {
        undo_reply()
    }
})

function go_to_reply(id, author_name) {
    var nav = $('#submit-comment');
    if (nav.length) {
        $('html, body').animate({scrollTop: nav.offset().top}, 800);
        $('#follow_id').val(id);
        $('#follow').val(author_name);
        $('#content').text("@" + author_name + " ")
    }
}

//Reset the follow value when refresh page
window.onload = function () {
    $('#follow_id').val(-1);
    $('#follow').val("");
}



