from database.models import UserCharacterStable, UserCharacterTemporary, Character, Episode, Scene
from django.db.models import OuterRef
from django.db.models.functions import Coalesce


def add_characters_to_episode_or_scene(names:list, episode:Episode=None, scene:Scene=None):
    if episode is None and scene is None:
        return
    
    if len(names) == 0:
        return
    
    created_objects = []

    base_filter = {}
    if episode:
        base_filter["episode"] = episode
    if scene:
        base_filter["scene"] = scene

    existing_characters = Character.objects.filter(name__in=names)
    existing_character_map = {c.name: c for c in existing_characters}
    existing_names = set(existing_character_map.keys())

    existing_stables = set(
        UserCharacterStable.objects.filter(
            **base_filter,
            character__name__in=existing_names
        ).values_list("character__name", flat=True)
    )

    existing_temporaries = set(
        UserCharacterTemporary.objects.filter(
            **base_filter,
            name__in=[n for n in names if n not in existing_names]
        ).values_list("name", flat=True)
    )

    already_created = existing_stables | existing_temporaries

    stable_bulk = []
    temporary_bulk = []

    for name in names:
        if name in already_created:
            continue  # skip if already exists

        kwargs = base_filter.copy()
        if episode:
            kwargs["episode"] = episode
        if scene:
            kwargs["scene"] = scene

        if name in existing_names:
            kwargs["character"] = existing_character_map[name]
            last_user_character = UserCharacterStable.objects.filter(
                character=existing_character_map[name].pk,
                user__isnull=False
            ).annotate(
                effective_deadline=Coalesce('episode__deadline', 'scene__deadline')
            ).order_by('-effective_deadline').first()
            kwargs["user"] = last_user_character.user
            stable_bulk.append(UserCharacterStable(**kwargs))
        else:
            kwargs["name"] = name
            temporary_bulk.append(UserCharacterTemporary(**kwargs))

    UserCharacterStable.objects.bulk_create(stable_bulk, batch_size=1000)
    UserCharacterTemporary.objects.bulk_create(temporary_bulk, batch_size=1000)

    created_objects.extend(stable_bulk + temporary_bulk)
    return created_objects