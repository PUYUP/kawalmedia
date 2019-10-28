import threading


class RequestMiddleware:
    def __init__(self, get_response, thread_local=threading.local()):
        self.get_response = get_response
        self.thread_local = thread_local

    # One-time configuration and initialization.
    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        self.thread_local.current_request = request

        # For security reason, set auth with middleware
        try:
            auth_code = request.META['HTTP_AUTHORIZATION']
        except KeyError:
            auth_code = None

        if auth_code is not None:
            session = request.session.get(auth_code, None)
            if session is not None:
                access = session['access']
                request.META['HTTP_AUTHORIZATION'] = 'Bearer ' + access

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
