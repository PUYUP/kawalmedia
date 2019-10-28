( function ($) {
    $( document ).ready( function () {
        'use strict';

        /***
         * CSRF Token
         */
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        $( document ).on( 'click', '#test', function ( e ) {
            $.ajax({
                url: 'http://localhost:8000/',
                method: 'POST',
                data: {
                    csrfmiddlewaretoken: getCookie('csrftoken'),
                },
                success: function (data) {
                    console.log(data);
                }
            });
        })
    });
})( jQuery );
