from database.models import Dubbing, UserCharacterStable, UserCharacterTemporary
from database.utils import get_character_user_type

def is_admin(user) -> bool:
    return user.has_perm("database.is_admin")

def manages_something(user):
    return is_admin(user) or Dubbing.objects.filter(manager=user).exists()

def get_character_user(type, char_id):
    uc = get_character_user_type(type)
    if uc is not None:
        return uc.objects.filter(id=char_id).first()
    return None