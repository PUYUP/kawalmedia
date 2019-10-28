( function( $ ) {
    $( document ).ready( function() {
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

        ClassicEditor
            .create( document.querySelector( '#id_description' ), {
                ckfinder: {
                    uploadUrl: '/api/knowledgebase/attachments/',
                    entity_index: '0',
                    entity_uuid: '3af7c402-a00f-4c03-ad69-a43f92a1d064',
                    headers: {
                        'X-CSRFTOKEN': getCookie('csrftoken'),
                    },
                }
            } )
            .catch( error => {
                console.error( error );
            } );
    } );
} )( django.jQuery );