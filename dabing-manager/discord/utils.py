from django.http import JsonResponse
from database.models import UserProfile, Dubbing
from frontend.utils import is_admin as ia

def validate_token(func):
    def wrapper(request, *args, **kwargs):
        token = request.GET.get("token") or request.POST.get("token")
        if token is None:
            return JsonResponse({"error": "Token is not defined"}, status=401)
        if not UserProfile.objects.filter(token=token).exists():
            return JsonResponse({"error": "Token is invalid"}, status=401)
        
        return func(request, *args, **kwargs)
    
    return wrapper

def is_admin(func):
    def wrapper(request, *args, **kwargs):
        if not ia(request.user):
            return JsonResponse({"error": "User is not Admin"}, status=403)
        
        return func(request, *args, **kwargs)
    
    return wrapper

def is_manager(request, dubbing):
    if dubbing is None:
        return False
    
    found_dubbing = Dubbing.objects.filter(id=int(dubbing))
    if not found_dubbing.exists():
        return False

    return found_dubbing.first().manager == request.user or ia(request.user)