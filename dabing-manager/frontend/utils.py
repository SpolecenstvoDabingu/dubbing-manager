from database.models import Dubbing, UserCharacterStable, UserCharacterTemporary
from database.utils import get_character_user_type
from django.contrib.auth.models import Permission
import re

def is_admin(user) -> bool:
    return user.has_perm("database.is_admin")

def is_superuser(user) -> bool:
    return user.is_superuser

def manages_something(user):
    return is_admin(user) or Dubbing.objects.filter(manager=user).exists()

def get_character_user(type, char_id):
    uc = get_character_user_type(type)
    if uc is not None:
        return uc.objects.filter(id=char_id).first()
    return None

def have_permissions_changed(user, new_perm_codenames, app_label='database'):
    current_perms = set(user.user_permissions.values_list('codename', flat=True))
    new_perms = set(new_perm_codenames)
    return current_perms, new_perms

def sanitize(name: str, replace_with: str='_') -> str:
    if not name:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', replace_with, name)