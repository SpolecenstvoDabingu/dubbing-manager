from django.shortcuts import render, redirect
from django.contrib.auth import logout
from core.utils import custom_render
from core.settings import LOCAL_ADDRESSES

def not_allowed(request, exception=None):
    if request.user.is_authenticated:
        logout(request)
    context = {"message": "You are not allowed to log in via Discord."}
    return custom_render(request, "discordoauth2/not_allowed.html", context, status=403)

def force_logout(request):
    logout(request)
    return redirect("home")

def login(request):
    host = request.get_host()
    show_local = any([host.startswith(address) for address in LOCAL_ADDRESSES])
    return custom_render(request, "discordoauth2/login.html", {"show_local": show_local})
