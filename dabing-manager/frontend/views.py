from django.contrib.auth.decorators import login_required, user_passes_test
from core.utils import custom_render
from django.shortcuts import redirect
from django.db.models import Prefetch
from database.models import Dubbing, Episode, Scene, UserCharacterStable, UserCharacterTemporary, UserCharacterBase, Character
from django.shortcuts import get_object_or_404
from django.http import Http404
from .utils import manages_something, is_admin, get_character_user
from database.utils import is_default_value
import json

@login_required
def home(request):
    user = request.user

    # Fetch both stable and temporary assignments for this user
    stable_qs = UserCharacterStable.objects.filter(user=user)
    temporary_qs = UserCharacterTemporary.objects.filter(user=user)

    # Prefetch related scene/episode objects for stable and temporary characters
    scenes = Scene.objects.prefetch_related(
        Prefetch('usercharacterstable', queryset=stable_qs, to_attr='user_stable'),
        Prefetch('usercharactertemporary', queryset=temporary_qs, to_attr='user_temp')
    ).select_related('dubbing')

    episodes = Episode.objects.prefetch_related(
        Prefetch('usercharacterstable', queryset=stable_qs, to_attr='user_stable'),
        Prefetch('usercharactertemporary', queryset=temporary_qs, to_attr='user_temp')
    ).select_related('dubbing')

    not_done = []
    done = []

    def get_assignment_status(obj):
        stable_done = all(uc.done for uc in getattr(obj, 'user_stable', []))
        temp_done = all(uc.done for uc in getattr(obj, 'user_temp', []))

        has_stable = bool(getattr(obj, 'user_stable', []))
        has_temp = bool(getattr(obj, 'user_temp', []))

        if not has_stable and not has_temp:
            return None  # Not assigned to user

        return stable_done and temp_done

    for scene in scenes:
        status = get_assignment_status(scene)
        if status is None:
            continue
        entry = {
            'type': 'scene',
            'object': scene,
            'dubbing': scene.dubbing,
        }
        (done if status else not_done).append(entry)

    for ep in episodes:
        status = get_assignment_status(ep)
        if status is None:
            continue
        entry = {
            'type': 'episode',
            'object': ep,
            'dubbing': ep.dubbing,
        }
        (done if status else not_done).append(entry)

    # Sort "not done" by earliest deadline
    not_done.sort(key=lambda x: x['object'].deadline)

    # Sort "done" by logic depending on type
    def done_sort_key(entry):
        obj = entry['object']
        if entry['type'] == 'episode':
            return (obj.season, obj.episode, obj.created)
        else:
            return obj.created

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
@user_passes_test(manages_something)
def stats(request):
    if is_admin(request.user):
        dubbings = Dubbing.objects.all()
    else:
        dubbings = Dubbing.objects.filter(manager=request.user)

    result_dubs = {}

    for dubbing in dubbings:
        episodes = []
        for ep in dubbing.episode.all():
            total = ep.usercharacterstable.count() + ep.usercharactertemporary.count()
            done = ep.usercharacterstable.filter(done=True).count() + ep.usercharactertemporary.filter(done=True).count()
            episodes.append({
                "id": ep.pk,
                "name": ep.name,
                "created": ep.created,
                "deadline": ep.deadline,
                "progress": f"{done}/{total}",
                "script": ep.id,
            })

            
        scenes = []
        for scene in dubbing.scene.all():
            total = scene.usercharacterstable.count() + scene.usercharactertemporary.count()
            done = scene.usercharacterstable.filter(done=True).count() + scene.usercharactertemporary.filter(done=True).count()
            scenes.append({
                "id": scene.pk,
                "name": scene.name,
                "created": scene.created,
                "deadline": scene.deadline,
                "progress": f"{done}/{total}",
                "script": scene.id,
            })

        print("dubbing id", dubbing.id)

        result_dubs[dubbing.name] = {
            "id": dubbing.id,
            "episodes": episodes,
            "scenes": scenes,
            "modify_dubbing_data": dubbing.get_modify_modal_fields_json()
        }


    return custom_render(request, "stats/dubbings.html", {
        "card": "stats",
        "dubbing_data": result_dubs,
        "add_dubbing_data": Dubbing.get_add_modal_fields_json(),
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
    for ep in dubbing.episode.all():
        total = ep.usercharacterstable.count() + ep.usercharactertemporary.count()
        done = ep.usercharacterstable.filter(done=True).count() + ep.usercharactertemporary.filter(done=True).count()
        episodes.append({
            "id": ep.pk,
            "name": ep.name,
            "created": ep.created,
            "deadline": ep.deadline,
            "progress": f"{done}/{total}",
            "script": ep.id,
            "modify_episode_data": filter_options(ep.get_modify_modal_fields_json(), dubbing.id),
        })

        
    scenes = []
    for scene in dubbing.scene.all():
        total = scene.usercharacterstable.count() + scene.usercharactertemporary.count()
        done = scene.usercharacterstable.filter(done=True).count() + scene.usercharactertemporary.filter(done=True).count()
        scenes.append({
            "id": scene.pk,
            "name": scene.name,
            "created": scene.created,
            "deadline": scene.deadline,
            "progress": f"{done}/{total}",
            "script": scene.id,
            "modify_scene_data": filter_options(scene.get_modify_modal_fields_json(), dubbing.id),
        })

        
    characters = Character.objects.filter(dubbing=dubbing)

    return custom_render(request, "stats/dubbing.html", {
        "dubbing": dubbing,
        "modify_dubbing_data": dubbing.get_modify_modal_fields_json(),
        "add_episode_data": filter_options(Episode.get_add_modal_fields_json(), dubbing.id),
        "add_scene_data": filter_options(Scene.get_add_modal_fields_json(), dubbing.id),
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

    stable_chars = UserCharacterStable.objects.filter(episode=episode).select_related('character', 'user')
    temporary_chars = UserCharacterTemporary.objects.filter(episode=episode).select_related('user')

    return custom_render(request, "stats/episode.html", {
        "episode": episode,
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

    stable_chars = UserCharacterStable.objects.filter(scene=scene).select_related('character', 'user')
    temporary_chars = UserCharacterTemporary.objects.filter(scene=scene).select_related('user')

    return custom_render(request, "stats/scene.html", {
        "scene": scene,
        "stable_chars": stable_chars,
        "temporary_chars": temporary_chars,
        "add_character_temp_data": UserCharacterTemporary.get_add_modal_fields_json(scene=scene),
        "add_character_stable_data": UserCharacterStable.get_add_modal_fields_json(scene=scene),
        "is_admin": is_admin(request.user)
    })