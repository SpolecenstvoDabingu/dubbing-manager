from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.utils import require_DELETE
from discord.utils import validate_token, is_manager, is_admin
from frontend.utils import is_admin as is_admin_f, get_character_user
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
from core.settingz.urls import NO_THUMBNAIL_URL
from database.utils import get_character_user_type
from datetime import datetime
from django.utils import timezone
from script.utils import handle_uploaded_script
from .utils import add_characters_to_episode_or_scene

from database.models import Dubbing, Episode, Scene, Character, UserCharacterStable, UserCharacterTemporary

@require_POST
@validate_token
@is_admin
def add_dubbing(request):
    name = request.POST.get("name")
    description = request.POST.get("description")
    urls = request.POST.get("urls")
    manager = request.POST.get("manager")

    if manager is None:
        return JsonResponse({"manager": "Manager needs to be set."}, status=400)

    manager_user = User.objects.get(id=int(manager))

    if manager_user is None:
        return JsonResponse({"manager": "Manager needs to exist."}, status=400)
    
    dubbing = Dubbing(name=str(name), description=str(description), urls=str(urls), manager=manager_user)

    try:
        dubbing.save(ia=is_admin_f(request.user))
        return JsonResponse({"sucess": True}, status=200)
    except IntegrityError as e:
        if 'UNIQUE constraint' in str(e.args):
            return JsonResponse({"dubbing": f"Dubbing name needs to be unique"}, status=400)
        return JsonResponse({"dubbing": f"Can't save dubbing because of: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"dubbing": f"Can't save dubbing because of: {e}"}, status=400)
    
@require_POST
@validate_token
def modify_dubbing(request, id):
    dubbing_old = Dubbing.objects.filter(id=id)
    if not dubbing_old.exists():
        return JsonResponse({"dubbing": "Dubbing you tried to modify does not exist."}, status=404)
    
    dubbing_old = dubbing_old.first()

    if not is_manager(request, dubbing_old.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)


    name = request.POST.get("name")
    description = request.POST.get("description")
    urls = request.POST.get("urls")
    manager = request.POST.get("manager")

    if manager is None:
        return JsonResponse({"manager": "Manager needs to be set."}, status=400)

    manager_user = User.objects.get(id=int(manager))

    if manager_user is None:
        return JsonResponse({"manager": "Manager needs to exist."}, status=400)
    
    save = False
    
    if dubbing_old.name != str(name):
        dubbing_old.name = str(name)
        save = True

    if dubbing_old.description != str(description):
        dubbing_old.description = str(description)
        save = True

    if dubbing_old.urls != str(urls):
        dubbing_old.urls = str(urls)
        save = True

    if dubbing_old.manager != manager_user:
        dubbing_old.manager = manager_user
        save = True
    
    if save:
        dubbing_old.save(ia=is_admin_f(request.user))

    return JsonResponse({"sucess": True}, status=200)

@require_POST
@validate_token
@is_admin
def delete_dubbing(request, id):
    dubbing = Dubbing.objects.get(id=id)
    if dubbing is None:
        return JsonResponse({"dubbing": "Dubbing you tried to modify does not exist."}, status=400)
    try:
        dubbing.delete()
    except Exception as e:
        return JsonResponse({"dubbing": f"Error occured while deleting dubbing: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=200)



@require_POST
@validate_token
def add_episode(request):
    name = request.POST.get("name")
    dubbing_id = request.POST.get("dubbing")
    started = request.POST.get("started")
    deadline = request.POST.get("deadline")
    season = request.POST.get("season")
    episode_number = request.POST.get("episode")
    urls = request.POST.get("urls")

    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return JsonResponse({"dubbing": "Selected dubbing does not exist."}, status=400)

    dubbing = dubbing.first()

    if not is_manager(request, dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)
    
    
    try:
        dt_started = datetime.fromisoformat(started)
        if timezone.is_naive(dt_started):
            dt_started = timezone.make_aware(dt_started)
    except (ValueError, TypeError):
        dt_started = None

    try:
        dt_deadline = datetime.fromisoformat(deadline)
        if timezone.is_naive(dt_deadline):
            dt_deadline = timezone.make_aware(dt_deadline)
    except (ValueError, TypeError):
        dt_deadline = None


    handled_file, characters_list = handle_uploaded_script(request.FILES.get("script"), dubbing_id=dubbing.id, dubbing_title=f"{dubbing}", serie_number=f"{int(season):02d}", episode_number=f"{int(episode_number):02d}", title=f"{name}")
    episode = Episode(
        name=str(name),
        dubbing=dubbing,
        started=dt_started,
        deadline=dt_deadline,
        season=int(season),
        episode=int(episode_number),
        script=handled_file,
        urls=str(urls),
    )

    try:
        episode.save(ia=is_admin_f(request.user))
        add_characters_to_episode_or_scene(characters_list, episode=episode)
        return JsonResponse({"sucess": True}, status=200)
    except Exception as e:
        return JsonResponse({"episode": f"Can't save episode because of: {e}"}, status=400)
    
@require_POST
@validate_token
def modify_episode(request, id):
    episode_old = Episode.objects.filter(id=id)
    if not episode_old.exists():
        return JsonResponse({"episode": "Episode you tried to modify does not exist."}, status=400)
    
    episode_old = episode_old.first()

    if not is_manager(request, episode_old.dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    name = request.POST.get("name")
    dubbing_id = request.POST.get("dubbing")
    started = request.POST.get("started")
    deadline = request.POST.get("deadline")
    season = request.POST.get("season")
    episode_number = request.POST.get("episode")
    urls = request.POST.get("urls")

    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return JsonResponse({"dubbing": "Selected dubbing does not exist."}, status=400)

    dubbing = dubbing.first()

    if not is_manager(request, dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    save = False

    if episode_old.name != name:
        episode_old.name = name
        save = True

    if episode_old.dubbing != dubbing:
        episode_old.dubbing = dubbing
        save = True

    if started != episode_old.started.isoformat() if episode_old.started else None:
        try:
            dt_started = datetime.fromisoformat(started)
            if timezone.is_naive(dt_started):
                dt_started = timezone.make_aware(dt_started)
        except (ValueError, TypeError):
            dt_started = None
        episode_old.started = dt_started
        save = True

    if deadline != episode_old.deadline.isoformat() if episode_old.deadline else None:
        try:
            dt_deadline = datetime.fromisoformat(deadline)
            if timezone.is_naive(dt_deadline):
                dt_deadline = timezone.make_aware(dt_deadline)
        except (ValueError, TypeError):
            dt_deadline = None
        episode_old.deadline = dt_deadline
        save = True

    if str(episode_old.season) != str(season):
        episode_old.season = int(season) if season else None
        save = True

    if str(episode_old.episode) != str(episode_number):
        episode_old.episode = int(episode_number) if episode_number else None
        save = True

    if episode_old.urls != urls:
        episode_old.urls = urls
        save = True

    if "script" in request.FILES:
        handled_file, characters_list = handle_uploaded_script(request.FILES["script"], dubbing_id=episode_old.dubbing.id, dubbing_title=f"{episode_old.dubbing}", serie_number=f"{int(episode_old.season):02d}", episode_number=f"{int(episode_old.episode):02d}", title=f"{episode_old.name}")
        add_characters_to_episode_or_scene(characters_list, episode=episode_old)
        if handled_file is not None:
            episode_old.script = handled_file
            save = True

    if save:
        episode_old.save(ia=is_admin_f(request.user))

    return JsonResponse({"success": True}, status=200)

@require_POST
@validate_token
@is_admin
def delete_episode(request, id):
    episode = Episode.objects.get(id=id)
    if episode is None:
        return JsonResponse({"episode": "Episode you tried to modify does not exist."}, status=400)
    try:
        episode.delete()
    except Exception as e:
        return JsonResponse({"episode": f"Error occured while deleting episode: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=400)



@require_POST
@validate_token
def add_scene(request):
    name = request.POST.get("name")
    dubbing_id = request.POST.get("dubbing")
    started = request.POST.get("started")
    deadline = request.POST.get("deadline")
    urls = request.POST.get("urls")

    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return JsonResponse({"dubbing": "Selected dubbing does not exist."}, status=400)

    dubbing = dubbing.first()

    if not is_manager(request, dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)
    
    try:
        dt_started = datetime.fromisoformat(started)
        if timezone.is_naive(dt_started):
            dt_started = timezone.make_aware(dt_started)
    except (ValueError, TypeError):
        dt_started = None
    
    try:
        dt_deadline = datetime.fromisoformat(deadline)
        if timezone.is_naive(dt_deadline):
            dt_deadline = timezone.make_aware(dt_deadline)
    except (ValueError, TypeError):
        dt_deadline = None
    
    
    handled_file, characters_list = handle_uploaded_script(request.FILES.get("script"), dubbing_id=dubbing.id, dubbing_title=f"{dubbing}", title=f"{name}")
    scene = Scene(
        name=str(name),
        dubbing=dubbing,
        started=dt_started,
        deadline=dt_deadline,
        script=handled_file,
        urls=str(urls),
    )

    try:
        scene.save(ia=is_admin_f(request.user))
        add_characters_to_episode_or_scene(characters_list, scene=scene)
        return JsonResponse({"sucess": True}, status=200)
    except Exception as e:
        return JsonResponse({"scene": f"Can't save scene because of: {e}"}, status=400)
    
@require_POST
@validate_token
def modify_scene(request, id):
    scene_old = Scene.objects.filter(id=id)
    if not scene_old.exists():
        return JsonResponse({"scene": "Scene you tried to modify does not exist."}, status=400)
    
    scene_old = scene_old.first()

    if not is_manager(request, scene_old.dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    name = request.POST.get("name")
    dubbing_id = request.POST.get("dubbing")
    started = request.POST.get("started")
    deadline = request.POST.get("deadline")
    urls = request.POST.get("urls")

    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return JsonResponse({"dubbing": "Selected dubbing does not exist."}, status=400)

    dubbing = dubbing.first()

    if not is_manager(request, dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    save = False

    if scene_old.name != name:
        scene_old.name = name
        save = True

    if scene_old.dubbing != dubbing:
        scene_old.dubbing = dubbing
        save = True

    if started != scene_old.started.isoformat() if scene_old.started else None:
        try:
            dt_started = datetime.fromisoformat(started)
            if timezone.is_naive(dt_started):
                dt_started = timezone.make_aware(dt_started)
        except (ValueError, TypeError):
            dt_started = None
        scene_old.started = dt_started
        save = True

    if deadline != scene_old.deadline.isoformat() if scene_old.deadline else None:
        try:
            dt_deadline = datetime.fromisoformat(deadline)
            if timezone.is_naive(dt_deadline):
                dt_deadline = timezone.make_aware(dt_deadline)
        except (ValueError, TypeError):
            dt_deadline = None
        scene_old.deadline = dt_deadline
        save = True

    if scene_old.urls != urls:
        scene_old.urls = urls
        save = True

    if "script" in request.FILES:
        handled_file, characters_list = handle_uploaded_script(request.FILES["script"], dubbing_id=scene_old.dubbing.id, dubbing_title=f"{scene_old.dubbing}", title=f"{scene_old.name}")
        add_characters_to_episode_or_scene(characters_list, scene=scene_old)
        if handled_file is not None:
            scene_old.script = handled_file
            save = True

    if save:
        scene_old.save(ia=is_admin_f(request.user))

    return JsonResponse({"success": True}, status=200)

@require_POST
@validate_token
@is_admin
def delete_scene(request, id):
    scene = Scene.objects.get(id=id)
    if scene is None:
        return JsonResponse({"scene": "Scene you tried to modify does not exist."}, status=400)
    try:
        scene.delete()
    except Exception as e:
        return JsonResponse({"scene": f"Error occured while deleting scene: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=200)




@require_POST
@validate_token
def add_character(request):
    dubbing_id = request.POST.get("dubbing")
    name = request.POST.get("name")
    description = request.POST.get("description")

    dubbing = Dubbing.objects.filter(id=dubbing_id)
    if not dubbing.exists():
        return JsonResponse({"dubbing": "Selected dubbing does not exist."}, status=400)

    dubbing = dubbing.first()

    if not is_manager(request, dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)
    
    character = Character(
        name=str(name),
        dubbing=dubbing,
        image=request.FILES.get("image", NO_THUMBNAIL_URL),
        description=str(description),
    )

    try:
        character.save()
        return JsonResponse({"sucess": True}, status=200)
    except Exception as e:
        return JsonResponse({"character": f"Can't save character because of: {e}"}, status=400)
    
@require_POST
@validate_token
def modify_character(request, id):
    character_old = Character.objects.filter(id=id)
    if not character_old.exists():
        return JsonResponse({"character": "Character you tried to modify does not exist."}, status=400)
    
    character_old = character_old.first()

    if not is_manager(request, character_old.dubbing.id) and not is_admin_f(request.user):
        return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    name = request.POST.get("name")
    description = request.POST.get("description")

    save = False

    if character_old.name != name:
        character_old.name = name
        save = True

    if character_old.description != description:
        character_old.description = description
        save = True

    if "image" in request.FILES:
        character_old.image = request.FILES["image"]
        save = True

    if save:
        character_old.save()

    return JsonResponse({"success": True}, status=200)

@require_POST
@validate_token
@is_admin
def character_make_stable(request, id):
    temporary_character = UserCharacterTemporary.objects.get(id=id)
    if temporary_character is None:
        return JsonResponse({"temporary_character": "Temporary character you tried to make stable does not exist."}, status=400)
    
    character = Character.objects.filter(name=temporary_character.name)
    if character.exists():
        return JsonResponse({"character": "Character you tried to make stable already exist."}, status=400)

    character = Character(
        dubbing=temporary_character.episode.dubbing if temporary_character.episode else temporary_character.scene.dubbing,
        name=temporary_character.name,
        image=temporary_character.image,
        description=temporary_character.description
    )

    user_character = UserCharacterStable(
        character=character,
        episode=temporary_character.episode,
        scene=temporary_character.scene,
        user=temporary_character.user,
        done=temporary_character.done
    )

    try:
        with transaction.atomic():
            character.save(ia=True)
            user_character.save()
            temporary_character.delete()
    except Exception as e:
        return JsonResponse({"character": f"Error occured while making character stable character: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=200)

@require_POST
@validate_token
@is_admin
def delete_character(request, id):
    character = Character.objects.get(id=id)
    if character is None:
        return JsonResponse({"character": "Character you tried to modify does not exist."}, status=400)
    try:
        character.delete()
    except Exception as e:
        return JsonResponse({"character": f"Error occured while deleting character: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=200)





@require_POST
@validate_token
def add_character_user(request, type):
    episode_id = request.POST.get("episode")
    scene_id = request.POST.get("scene")
    user_id = request.POST.get("user")

    if episode_id is None and scene_id is None:
        return JsonResponse({"episode_scene": "Episode or Scene needs to be specified."}, status=400)
    
    if user_id is None:
        return JsonResponse({"user": "User needs to be specified."}, status=400)
    
    episode = None
    if episode_id is not None:
        episode = Episode.objects.filter(id=episode_id)
        if not episode.exists():
            return JsonResponse({"episode": "Episode does not exists."}, status=404)
        episode = episode.first()
        if not is_manager(request, episode.dubbing.id) and not is_admin_f(request.user):
            return JsonResponse({"access": "You don't have neccessary access"}, status=403)
    
    scene = None
    if scene_id is not None:
        scene = Scene.objects.filter(id=scene_id)
        if not scene.exists():
            return JsonResponse({"scene": "Scene does not exists."}, status=404)
        scene = scene.first()
        if not is_manager(request, scene.dubbing.id) and not is_admin_f(request.user):
            return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    user = User.objects.filter(id=user_id)
    if not user.exists():
        return JsonResponse({"user": "User does not exists."}, status=404)
    user = user.first()


    if type == "static":
        character_id = request.POST.get("character")

        if character_id is None:
            return JsonResponse({"character": "Character needs to be specified."}, status=400)
        
        character = Character.objects.filter(id=character_id)
        if not character.exists():
            return JsonResponse({"character": "Character does not exists."}, status=404)
        character = character.first()

        user_character = UserCharacterStable(
            character=character,
            episode=episode,
            scene=scene,
            user=user,
        )
    elif type == "temporary":
        name = request.POST.get("name")
        description = request.POST.get("description")

        if name is None:
            return JsonResponse({"name": "Name needs to be specified."}, status=400)

        user_character = UserCharacterTemporary(
            name=str(name),
            image=request.FILES.get("image", NO_THUMBNAIL_URL),
            description=str(description),
            episode=episode,
            scene=scene,
            user=user,
        )

    else:
        return JsonResponse({"type": "Type needs to be 'static' or 'temporary'."}, status=400)
    
    try:
        user_character.save()
        return JsonResponse({"sucess": True}, status=200)
    except Exception as e:
        return JsonResponse({"user_character": f"Can't save character -> user because of: {e}"}, status=400)
    

@require_POST
@validate_token
def modify_character_user(request, type, id):
    user_character = get_character_user(type, id)
    if user_character is None:
        return JsonResponse({"character_user": "Character -> User you tried to modify does not exist."}, status=400)

    episode_id = request.POST.get("episode")
    scene_id = request.POST.get("scene")
    user_id = request.POST.get("user")

    if episode_id is None and scene_id is None:
        return JsonResponse({"episode_scene": "Episode or Scene needs to be specified."}, status=400)
    
    if user_id is None:
        return JsonResponse({"user": "User needs to be specified."}, status=400)
    
    episode = None
    if episode_id is not None:
        episode = Episode.objects.filter(id=episode_id)
        if not episode.exists():
            return JsonResponse({"episode": "Episode does not exists."}, status=404)
        episode = episode.first()
        if not is_manager(request, episode.dubbing.id) and not is_admin_f(request.user):
            return JsonResponse({"access": "You don't have neccessary access"}, status=403)
    
    scene = None
    if scene_id is not None:
        scene = Scene.objects.filter(id=scene_id)
        if not scene.exists():
            return JsonResponse({"scene": "Scene does not exists."}, status=404)
        scene = scene.first()
        if not is_manager(request, scene.dubbing.id) and not is_admin_f(request.user):
            return JsonResponse({"access": "You don't have neccessary access"}, status=403)

    user = User.objects.filter(id=user_id)
    if not user.exists():
        return JsonResponse({"user": "User does not exists."}, status=404)
    user = user.first()

    save = False

    if type == "stable":
        if user_character.episode != episode:
            user_character.episode = episode
            save = True
        
        if user_character.scene != scene:
            user_character.scene = scene
            save = True
        
        if user_character.user != user:
            user_character.user = user
            save = True
    elif type == "temporary":
        name = request.POST.get("name")
        description = request.POST.get("description")

        if name is None:
            return JsonResponse({"name": "Name needs to be specified."}, status=400)
        
        if user_character.name != str(name):
            user_character.name = str(name)
            save = True

        if "image" in request.FILES:
            user_character.image = request.FILES["image"]
            save = True
        
        if user_character.description != str(description):
            user_character.description = str(description)
            save = True
        
        if user_character.episode != episode:
            user_character.episode = episode
            save = True
        
        if user_character.scene != scene:
            user_character.scene = scene
            save = True
        
        if user_character.user != user:
            user_character.user = user
            save = True
        
    else:
        return JsonResponse({"type": "Type needs to be 'static' or 'temporary'."}, status=400)
    
    try:
        if save:
            user_character.save()
        return JsonResponse({"sucess": True}, status=200)
    except Exception as e:
        return JsonResponse({"user_character": f"Can't save character -> user because of: {e}"}, status=400)

@require_POST
@validate_token
@is_admin
def delete_character_user(request, type, id):
    chu = get_character_user(type, id)
    if chu is None:
        return JsonResponse({"character_user": "Character -> User you tried to modify does not exist."}, status=400)
    try:
        chu.delete()
    except Exception as e:
        return JsonResponse({"character_user": f"Error occured while deleting character: {e}"}, status=400)

    return JsonResponse({"sucess": True}, status=200)




@login_required
def hand_over(request, type, char_id):
    character_user = get_character_user(type, char_id)
    if character_user is None:
        return redirect('stats')
    
    if character_user.user == request.user or is_admin(request.user):
        character_user.done = True
        character_user.save()

    if character_user.episode:
        return redirect("stats_episode", character_user.episode.id)
    
    if character_user.scene:
        return redirect("stats_scene", character_user.scene.id)
    
    return redirect('stats')

@login_required
def unhand_over(request, type, char_id):
    character_user = get_character_user(type, char_id)
    if character_user is None:
        return redirect('stats')
    
    if character_user.user == request.user or is_admin(request.user):
        character_user.done = False
        character_user.save()

    if character_user.episode:
        eID = character_user.episode.id
        return redirect("stats_episode", eID)
    
    if character_user.scene:
        sID = character_user.scene.id
        return redirect("stats_scene", sID)
    
    return redirect('stats')