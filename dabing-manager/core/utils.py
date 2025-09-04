from django.shortcuts import render, redirect
import secrets
from django.db import models
from datetime import date
from . import settings
import re
from database.utils import get_user_discord_username, timezone
from django.views.decorators.http import require_http_methods

def redirect_to_home(request):
    return redirect('home')

def generate_unique_token(model:models.Model):
    while True:
        token = secrets.token_hex(32)
        if not model.objects.filter(token=token).exists():
            return token
        
def sanitize_ascii(input_string: str) -> str:
    sanitized = input_string.replace(' ', '_')
    sanitized = ''.join(c if ord(c) < 128 else '_' for c in sanitized)
    sanitized = re.sub(r'[^A-Za-z0-9_-]', '_', sanitized)
    return sanitized


def custom_render(request, template_name, context={}, status=200):
    user = request.user
    username = get_user_discord_username(user)

    default_context = {
        'year': date.today().strftime("%Y"),
        'base_url': f'{request.scheme}://{request.get_host()}',
        'instance_name': settings.INSTANCE_NAME,
        'community_name': settings.COMMUNITY_NAME,
        'languages': settings.LANGUAGES,
        'LOGO_IMG_URL': settings.LOGO_IMG_URL,
        'LOGO_ICON_URL': settings.LOGO_ICON_URL,
        'username': username,
    }

    context.update(default_context)
    return render(request, template_name, context, status=status)

require_DELETE = require_http_methods(["DELETE"])

require_GET_or_POST = require_http_methods(["GET", "POST"])