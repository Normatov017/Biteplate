from .audit import set_current_user


class AuditUserMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response


    def __call__(self, request):

        set_current_user(
            request.user
            if request.user.is_authenticated
            else None
        )

        response = self.get_response(request)

        set_current_user(None)

        return response
