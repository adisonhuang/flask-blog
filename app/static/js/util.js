function gethits(id, out) {
    $.ajax({
        type: "get",
        cache: false,
        url: '/api/get_hits/?id=' + id,
        timeout: 20000,
        error: function () {
            $('#' + out).html('failed');
        },
        success: function (t) {
            $('#' + out).html(t);
        }
    })
}