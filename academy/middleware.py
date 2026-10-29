class FeePaymentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass fee check completely and process response directly
        response = self.get_response(request)
        return response
