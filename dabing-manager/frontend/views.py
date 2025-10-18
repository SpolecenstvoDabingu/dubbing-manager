from django.contrib.auth.decorators import login_required, user_passes_test
from core.utils import custom_render
from django.shortcuts import redirect
from django.db.models import Count, OuterRef, Subquery, Prefetch, Case, When, IntegerField, Value
from django.db.models.functions import Coalesce
from database.models import Dubbing, Episode, Scene, UserCharacterStable, UserCharacterTemporary, UserCharacterBase, Character, UserProfile
from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.views.decorators.http import require_POST
from .utils import manages_something, is_admin, get_character_user, is_superuser, have_permissions_changed, sanitize, to_utc_iso
from database.utils import is_default_value, timezone
import json
from core.settingz.discord_commands import EPISODE_ANNOUNCEMENT, SCENE_ANNOUNCEMENT, EPISODE_NOTIFY, SCENE_NOTIFY

@login_required
def home(request):
    user = request.user

    stable_qs = UserCharacterStable.objects.filter(user=user)
    temporary_qs = UserCharacterTemporary.objects.filter(user=user)

    scenes = Scene.objects.prefetch_related(
        Prefetch('usercharacterstable', queryset=stable_qs, to_attr='user_stable'),
        Prefetch('usercharactertemporary', queryset=temporary_qs, to_attr='user_temp')
    ).select_related('dubbing').filter(started__lte=timezone.now())

    episodes = Episode.objects.prefetch_related(
        Prefetch('usercharacterstable', queryset=stable_qs, to_attr='user_stable'),
        Prefetch('usercharactertemporary', queryset=temporary_qs, to_attr='user_temp')
    ).select_related('dubbing').filter(started__lte=timezone.now())

    not_done = []
    done = []

    def get_assignment_status(obj):
        stable_done = all(uc.done for uc in getattr(obj, 'user_stable', []))
        temp_done = all(uc.done for uc in getattr(obj, 'user_temp', []))

        has_stable = bool(getattr(obj, 'user_stable', []))
        has_temp = bool(getattr(obj, 'user_temp', []))

        if not has_stable and not has_temp:
            return None

        return stable_done and temp_done

    for scene in scenes:
        status = get_assignment_status(scene)
        if status is None:
            continue
        entry = {
            'type': 'scene',
            'object': {
                "id": scene.id,
                "name": scene.name,
                "cover": scene.cover,
                "started": to_utc_iso(scene.started),
                "deadline": to_utc_iso(scene.deadline),
                "created": to_utc_iso(scene.created),
                "dubbing": scene.dubbing,
                "user_characters": [
                    {
                        "name": uc.character.name if isinstance(uc, UserCharacterStable) else uc.name,
                        "user": request.user,
                        "done": uc.done,
                        "type": "stable" if isinstance(uc, UserCharacterStable) else "temporary",
                        "image": uc.character.image.url if isinstance(uc, UserCharacterStable) else uc.image.url
                    } for uc in list(scene.usercharacterstable.filter(user=request.user)) + list(scene.usercharactertemporary.filter(user=request.user))
                ]
            },
            'dubbing': scene.dubbing,
        }
        (done if status else not_done).append(entry)

    for ep in episodes:
        status = get_assignment_status(ep)
        if status is None:
            continue
        entry = {
            'type': 'episode',
            'object': {
                "id": ep.id,
                "name": ep.name,
                "cover": ep.cover,
                "started": to_utc_iso(ep.started),
                "deadline": to_utc_iso(ep.deadline),
                "created": to_utc_iso(ep.created),
                "dubbing": ep.dubbing,
                "user_characters": [
                    {
                        "name": uc.character.name if isinstance(uc, UserCharacterStable) else uc.name,
                        "user": request.user,
                        "done": uc.done,
                        "type": "stable" if isinstance(uc, UserCharacterStable) else "temporary",
                        "image": uc.character.image.url if isinstance(uc, UserCharacterStable) else uc.image.url
                    } for uc in list(ep.usercharacterstable.filter(user=request.user)) + list(ep.usercharactertemporary.filter(user=request.user))
                ]
            },
            'dubbing': ep.dubbing,
        }
        (done if status else not_done).append(entry)

    not_done.sort(key=lambda x: x['object'].get("deadline"))

    def done_sort_key(entry):
        obj = entry['object']
        if entry['type'] == 'episode':
            return (int(obj.get("season", 1)), int(obj.get("episode", 1)), obj.get("created"))
        else:
            return (1, 1, obj.get("created"))

    done.sort(key=done_sort_key)

    return custom_render(request, "home.html", {
        "not_done": not_done,
        "done": done,
    })

@login_required
def download_script(request, obj_type, obj_id):
    if obj_type == 'episode':
        obj = get_object_or_404(Episode, pk=obj_id)
    elif obj_type == 'scene':
        obj = get_object_or_404(Scene, pk=obj_id)
    else:
        raise Http404("Invalid type")

    return obj.get_script_download_response()


@login_required
def stats(request):
    i_a = is_admin(request.user)
    dubbings = Dubbing.objects.order_by("name").all()
    d_now = timezone.now()

    result_dubs = {}

    for dubbing in dubbings:
        episodes = []
        for ep in dubbing.episode.order_by("season", "episode", "name").all():
            if not i_a and d_now < ep.started:
                continue
            total = ep.usercharacterstable.count() + ep.usercharactertemporary.count()
            done = ep.usercharacterstable.filter(done=True).count() + ep.usercharactertemporary.filter(done=True).count()
            episodes.append({
                "id": ep.pk,
                "name": ep.name,
                "cover": ep.cover or dubbing.cover,
                "created": to_utc_iso(ep.created),
                "started": to_utc_iso(ep.started),
                "deadline": to_utc_iso(ep.deadline),
                "progress": f"{done}/{total}",
                "script": ep.id,
            })

            
        scenes = []
        for scene in dubbing.scene.order_by("name").all():
            if not i_a and d_now < scene.started:
                continue
            total = scene.usercharacterstable.count() + scene.usercharactertemporary.count()
            done = scene.usercharacterstable.filter(done=True).count() + scene.usercharactertemporary.filter(done=True).count()
            scenes.append({
                "id": scene.pk,
                "name": scene.name,
                "cover": scene.cover or dubbing.cover,
                "created": to_utc_iso(scene.created),
                "started": to_utc_iso(scene.started),
                "deadline": to_utc_iso(scene.deadline),
                "progress": f"{done}/{total}",
                "script": scene.id,
            })

        result_dubs[dubbing.name] = {
            "id": dubbing.id,
            "cover": dubbing.cover,
            "episodes": episodes,
            "scenes": scenes,
            "modify_dubbing_data": dubbing.get_modify_modal_fields_json(is_admin=is_admin(request.user))
        }


    return custom_render(request, "stats/dubbings.html", {
        "card": "stats",
        "dubbing_data": result_dubs,
        "add_dubbing_data": Dubbing.get_add_modal_fields_json(is_admin=is_admin(request.user)),
    })

@login_required
def stats_dubbing(request, dubbing_id):
    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return redirect("stats")
    
    dubbing = dubbing.first()
    

    def filter_options(obj, key):
        new_obj = []
        for fi in (json.loads(obj)):
            if fi.get("name") == "dubbing":
                temp = {}
                for ik, ii in fi.items():
                    if ik == "options":
                        temp[ik] = [item for item in ii if item.get("value") == key]
                    else:
                        temp[ik] = ii
                new_obj.append(temp)
            else:
                new_obj.append(fi)

        return json.dumps(new_obj)
    
    episodes = []
    for ep in dubbing.episode.order_by("season", "episode", "name") if is_admin(request.user) or dubbing.manager == request.user else dubbing.episode.order_by("season", "episode", "name").filter(started__lte=timezone.now()):
        total = ep.usercharacterstable.count() + ep.usercharactertemporary.count()
        done = ep.usercharacterstable.filter(done=True).count() + ep.usercharactertemporary.filter(done=True).count()
        episodes.append({
            "id": ep.pk,
            "name": ep.name,
            "cover": ep.cover or dubbing.cover,
            "created": to_utc_iso(ep.created),
            "started": to_utc_iso(ep.started),
            "deadline": to_utc_iso(ep.deadline),
            "progress": f"{done}/{total}",
            "script": ep.id,
            "modify_episode_data": filter_options(ep.get_modify_modal_fields_json(is_admin(request.user)), dubbing.id),
        })

        
    scenes = []
    for scene in dubbing.scene.order_by("name") if is_admin(request.user) or dubbing.manager == request.user else dubbing.scene.order_by("name").filter(started__lte=timezone.now()):
        total = scene.usercharacterstable.count() + scene.usercharactertemporary.count()
        done = scene.usercharacterstable.filter(done=True).count() + scene.usercharactertemporary.filter(done=True).count()
        scenes.append({
            "id": scene.pk,
            "name": scene.name,
            "cover": scene.cover or dubbing.cover,
            "created": to_utc_iso(scene.created),
            "started": to_utc_iso(scene.started),
            "deadline": to_utc_iso(scene.deadline),
            "progress": f"{done}/{total}",
            "script": scene.id,
            "modify_scene_data": filter_options(scene.get_modify_modal_fields_json(is_admin(request.user)), dubbing.id),
        })


    latest_user_subquery = UserCharacterStable.objects.filter(
        character=OuterRef('pk'),
        user__isnull=False
    ).annotate(
        effective_deadline=Coalesce('episode__deadline', 'scene__deadline'),
        effective_started=Coalesce('episode__started', 'scene__started')
    ).filter(effective_started__lte=timezone.now()).order_by('-effective_deadline').values('user_id')[:1]
        
    characters = Character.objects.filter(dubbing=dubbing).annotate(
        usage_count=Count('user'),
        last_user_id=Subquery(latest_user_subquery)
    ).order_by("-usage_count", "name")

    user_map = {
        user.id: user for user in User.objects.filter(id__in=[c.last_user_id for c in characters if c.last_user_id])
    }

    for c in characters:
        c.last_user = user_map.get(c.last_user_id)

    user_id_admin = is_admin(request.user)
    return custom_render(request, "stats/dubbing.html", {
        "dubbing": dubbing,
        "modify_dubbing_data": dubbing.get_modify_modal_fields_json(is_admin=is_admin(request.user)),
        "add_episode_data": filter_options(Episode.get_add_modal_fields_json(user_id_admin), dubbing.id),
        "add_scene_data": filter_options(Scene.get_add_modal_fields_json(user_id_admin), dubbing.id),
        "add_character_data": Character.get_add_modal_fields_json(dubbing),
        "episodes": episodes,
        "scenes": scenes,
        "characters": characters,
        "is_admin": is_admin(request.user)
    })

@login_required
def stats_episode(request, episode_id):
    episode = Episode.objects.filter(id=episode_id)
    if not episode.exists():
        return redirect("stats")

    episode = episode.first()

    stable_chars = UserCharacterStable.objects.filter(episode=episode).annotate(
        priority=Case(
            When(user=request.user, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by("priority", "character__name").select_related('character', 'user')
    temporary_chars = UserCharacterTemporary.objects.filter(episode=episode).order_by("name").select_related('user')

    return custom_render(request, "stats/episode.html", {
        "episode": episode,
        "announcement_command": EPISODE_ANNOUNCEMENT(episode.id),
        "notify_command": EPISODE_NOTIFY(episode.id),
        "stable_chars": stable_chars,
        "temporary_chars": temporary_chars,
        "add_character_temp_data": UserCharacterTemporary.get_add_modal_fields_json(episode=episode),
        "add_character_stable_data": UserCharacterStable.get_add_modal_fields_json(episode=episode),
        "is_admin": is_admin(request.user)
    })

@login_required
def stats_scene(request, scene_id):
    scene = Scene.objects.filter(id=scene_id)
    if not scene.exists():
        return redirect("stats")
    
    scene = scene.first()

    stable_chars = UserCharacterStable.objects.filter(scene=scene).annotate(
        priority=Case(
            When(user=request.user, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by("priority", "character__name").select_related('character', 'user')
    temporary_chars = UserCharacterTemporary.objects.filter(scene=scene).order_by("name").select_related('user')

    return custom_render(request, "stats/scene.html", {
        "scene": scene,
        "announcement_command": SCENE_ANNOUNCEMENT(scene.id),
        "notify_command": SCENE_NOTIFY(scene.id),
        "stable_chars": stable_chars,
        "temporary_chars": temporary_chars,
        "add_character_temp_data": UserCharacterTemporary.get_add_modal_fields_json(scene=scene),
        "add_character_stable_data": UserCharacterStable.get_add_modal_fields_json(scene=scene),
        "is_admin": is_admin(request.user)
    })




@login_required
@user_passes_test(is_superuser)
def manage_users(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        try:
            user = User.objects.get(id=user_id)
            if action == "regenerate":
                user.profile.regenerate_token()
                print(request, f"Token regenerated for {user.username}.")
        except User.DoesNotExist:
            print(request, "User not found.")

        return redirect("manage_users")

    users = sorted([u for u in User.objects.select_related("profile").filter(social_auth__provider='discord') if u.discord_display_name], key=lambda u: (sanitize(u.discord_display_name, "").lower(), sanitize(u.discord_display_name, "")))
    role_choices = UserProfile._meta.permissions
    return custom_render(request, "manager/users.html", {
        "users": users,
        "user_permissions": [f"database.{perm}" for perm in role_choices],
        "role_choices": role_choices,
        })

@login_required
@require_POST
@user_passes_test(is_superuser)
def update_user(request, id):
    user = User.objects.filter(id=id).first()
    if user is None:
        return JsonResponse({'error': "User does not exists"}, status=404)
    
    username = request.POST.get("username")
    if username is None or len(username) == 0:
        return JsonResponse({'error': "User username can not be blank"}, status=400)
    
    email = request.POST.get("email")
    selected_roles = request.POST.getlist('role[]')

    save = False

    if user.username != username:
        user.username = username
        save = True

    if user.email != email:
        user.email = email
        save = True

    if have_permissions_changed(user, selected_roles):
        permissions = Permission.objects.filter(
            content_type__app_label="database",
            codename__in=selected_roles
        )
        user.user_permissions.set(permissions)
        save = True

    if save:
        user.save()

    return JsonResponse({'success': True}, status=200)
