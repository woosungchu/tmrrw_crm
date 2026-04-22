class CompanyContextMiddleware:
    """로그인된 유저의 company 를 request 에 자동 주입.
    view 에서 request.company 로 바로 접근 가능."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            request.company = getattr(request.user, "company", None)
        return self.get_response(request)
