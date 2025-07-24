from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

class RestrictAdminMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/admin/'):
            if not request.user.is_authenticated:
                return None
            if not request.user.is_superuser:
                return HttpResponseForbidden("You don't have required permissions.")
        return None
