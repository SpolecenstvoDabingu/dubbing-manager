import ipaddress
from django.contrib.auth import authenticate
from django.http import HttpResponseForbidden, HttpResponseRedirect
from social_core.exceptions import AuthForbidden
from django.urls import reverse

class LocalSuperuserLoginRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/login') and request.method == 'POST':
            ip = request.META.get('REMOTE_ADDR')
            try:
                ip_addr = ipaddress.ip_address(ip)
                is_local = ip_addr.is_loopback or ip == '127.0.0.1'
            except Exception:
                is_local = False

            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)

            if user and user.is_superuser and not is_local:
                return HttpResponseForbidden("Superuser login allowed only from localhost.")

        return self.get_response(request)