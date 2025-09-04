import hashlib
import os, re
from django.utils.deconstruct import deconstructible
from core.settingz.paths import IMAGES_PATH
from datetime import timedelta
from django.utils import timezone
from django.db.models.fields import Field
from discordoauth2.utils import get_discord_username_from_id
from django.utils.html import escape
from datetime import datetime, timezone as dt_timezone

MARKDOWN_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)', re.IGNORECASE)

@deconstructible
class HashedImagePath:
    def __call__(self, instance, filename):
        # Get the file from the instance
        file = instance.image

        # Read file content to hash
        file.open()
        file_content = file.read()
        file.seek(0)

        # Compute hash (e.g., SHA256 or MD5)
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Extract file extension
        ext = os.path.splitext(filename)[1].lower()

        # Define the final path
        return f"images/{file_hash}{ext}"
    
@deconstructible
class HashedFilePath:
    def __call__(self, instance, filename):
        file = getattr(instance, self.field_name)

        if file.closed:
            file.open()
        file.seek(0)
        content = file.read()
        file.seek(0)

        file_hash = hashlib.sha256(content).hexdigest()
        ext = os.path.splitext(filename)[1].lower()

        return f"{self.path_name}/{file_hash}{ext}"

    def __init__(self, field_name, path_name="files"):
        self.field_name = field_name
        self.path_name = path_name

def today():
    return timezone.now()
    
def one_week_from_now():
    return today() + timedelta(weeks=1)

def three_days_from_now():
    return today() + timedelta(days=3)
    
def one_week_from(time:timezone):
    return time + timedelta(weeks=1)

def three_days_from(time:timezone):
    return time + timedelta(days=3)

def is_default_value(field: Field, value) -> bool:
    if not hasattr(field, 'default'):
        return False

    # Handle callables (e.g., default=datetime.now)
    default = field.default() if callable(field.default) else field.default

    return value == default

def is_local_user(user) -> bool:
    return not user.social_auth.filter(provider="discord").exists()

def get_user_discord_username(user) -> str:
    try:
        if user.is_authenticated:
            if is_local_user(user):
                return user.username
            else:
                social = user.social_auth.get(provider="discord")
                return get_discord_username_from_id(social.uid).display_name if social is not None else user.username
    except:
        return "Unknown"
    
def sanitize_markdown_links(text, is_admin=False):
    if not isinstance(text, str):
        return text

    if is_admin:
        return text
    
    def replace_markdown(match):
        label = match.group(1)
        url = match.group(2)
        return f'{label} {url}'

    return MARKDOWN_LINK_RE.sub(replace_markdown, text)

def get_character_user_type(type:str):
    from .models import UserCharacterStable, UserCharacterTemporary
    if type == "stable":
        return UserCharacterStable
    elif type == "temporary":
        return UserCharacterTemporary
    return None


def to_utc_iso(dt: datetime, as_string: bool = False, is_start: bool = False) -> str | datetime | None:
    if not dt:
        return None
    tz = dt.tzinfo
    if is_start:
        dt = dt + timedelta(hours=12)
    else:
        dt = dt - timedelta(hours=12)
    dt_aware = timezone.make_aware(dt, tz, is_dst=None) if timezone.is_naive(dt) else dt
    if as_string:
        return dt_aware.strftime("%Y-%m-%d")
    return dt_aware