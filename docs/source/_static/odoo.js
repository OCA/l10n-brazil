document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('keypress', function (e) {
        if (e.target !== document && e.target !== document.body) { return; }
        if (e.metaKey || e.ctrlKey) { return; }
        if (e.charCode !== 102 && e.keyCode !== 102) { return; }
        if (!isFullscreen()) {
            requestFullscreen();
        } else {
            exitFullscreen();
        }
    });
});

function isFullscreen() {
    return document.fullscreenElement
        || document.webkitFullscreenElement
        || document.mozFullScreenElement
        || document.msFullscreenElement;
}

function requestFullscreen() {
    var el = document.documentElement;
    if (el.requestFullscreen) {
        el.requestFullscreen(1);
    } else if(el.webkitRequestFullscreen) {
        el.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
    } else if(el.mozRequestFullScreen) {
        el.mozRequestFullScreen();
    } else if(el.msRequestFullscreen) {
        el.msRequestFullscreen();
    }
}

function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if(document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if(document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    } else if(document.msExitFullscreen) {
        document.msExitFullscreen();
    }
}
