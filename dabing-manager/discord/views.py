from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .utils import validate_token, is_admin
from .models import DiscordUser
from database.models import UserCharacterStable, UserCharacterTemporary
import json
from core.settingz.config import EXTERNAL_URL
from core.utils import require_GET_or_POST

from database.models import Episode, Scene

@csrf_exempt
@require_POST
@validate_token
@is_admin
def sync_users(request):
    try:
        data = (json.loads(request.body)).get("data")
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not isinstance(data, list):
        return JsonResponse({"error": "Expected a list of users"}, status=400)
    
    # Extract incoming IDs as strings
    incoming_ids = {str(entry.get("id")) for entry in data if entry.get("id")}

    # Fetch all existing users
    existing_users_qs = DiscordUser.objects.all()
    existing_users = {user.discord_id: user for user in existing_users_qs}

    to_create = []
    to_update = []

    for entry in data:
        discord_id = str(entry.get("id"))
        display_name = entry.get("name")
        avatar = entry.get("avatar")

        if not (discord_id and display_name and avatar):
            continue

        if discord_id in existing_users:
            user = existing_users[discord_id]
            if user.display_name != display_name or user.avatar != avatar:
                user.display_name = display_name
                user.avatar = avatar
                to_update.append(user)
        else:
            to_create.append(DiscordUser(
                discord_id=discord_id,
                display_name=display_name,
                avatar=avatar
            ))

    if to_create:
        DiscordUser.objects.bulk_create(to_create, batch_size=500)

    if to_update:
        DiscordUser.objects.bulk_update(to_update, ["display_name", "avatar"], batch_size=500)

    # Delete users not in incoming_ids
    to_delete = [user for user_id, user in existing_users.items() if user_id not in incoming_ids]
    deleted_count = 0
    if to_delete:
        deleted_count = len(to_delete)
        DiscordUser.objects.filter(id__in=[user.id for user in to_delete]).delete()

    return JsonResponse({
        "created": len(to_create),
        "updated": len(to_update),
        "deleted": deleted_count,
        "total_processed": len(data)
    }, status=200)

@csrf_exempt
@require_POST
@validate_token
@is_admin
def add_users(request):
    try:
        data = (json.loads(request.body)).get("data")
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not isinstance(data, list):
        return JsonResponse({"error": "Expected a list of users"}, status=400)
    
    
    existing_users = {
        user.discord_id: user for user in DiscordUser.objects.filter(discord_id__in=[str(d["id"]) for d in data])
    }

    to_create = []
    to_update = []


    for entry in data:
        discord_id = str(entry.get("id"))
        display_name = entry.get("name")
        avatar = entry.get("avatar")

        if not (discord_id and display_name and avatar):
            continue

        if discord_id in existing_users:
            user = existing_users[discord_id]
            if user.display_name != display_name or user.avatar != avatar:
                user.display_name = display_name
                user.avatar = avatar
                to_update.append(user)
        else:
            to_create.append(DiscordUser(
                discord_id=discord_id,
                display_name=display_name,
                avatar=avatar
            ))

    if to_create:
        DiscordUser.objects.bulk_create(to_create, batch_size=500)

    if to_update:
        DiscordUser.objects.bulk_update(to_update, ["display_name", "avatar"], batch_size=500)

    return JsonResponse({
        "created": len(to_create),
        "updated": len(to_update),
        "total_processed": len(data)
    }, status=200)


@csrf_exempt
@require_POST
@validate_token
@is_admin
def remove_users(request):
    try:
        data = (json.loads(request.body)).get("data")
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not isinstance(data, list):
        return JsonResponse({"error": "Expected a list of users"}, status=400)
    
    # Extract discord IDs from received data
    discord_ids_to_delete = [str(d.get("id")) for d in data if d.get("id")]

    # Delete users with these discord IDs
    deleted_count, _ = DiscordUser.objects.filter(discord_id__in=discord_ids_to_delete).delete()

    return JsonResponse({
        "deleted": deleted_count,
        "total_received": len(discord_ids_to_delete)
    }, status=200)


@csrf_exempt
@require_GET
@validate_token
@is_admin
def get_announce_data(request, type, id):
    if type not in ("episode", "scene"):
        return JsonResponse({"error": "Type needs to be 'episode' or 'scene'"}, status=400)
    try:
        if type == "episode":
            episode = Episode.objects.filter(id=id).first()
            if episode is None:
                return JsonResponse({"error": "Episode not found"}, status=404)
            
            dubbers = []

            for e_dubbers in episode.usercharacterstable.all():
                dubbers.append({
                    "character_name": f"{e_dubbers.character}",
                    "user_id": f"{e_dubbers.user.social_auth.filter(provider='discord').first().uid}",
                })

            for e_dubbers in episode.usercharactertemporary.all():
                dubbers.append({
                    "character_name": f"{e_dubbers.name}",
                    "user_id": f"{e_dubbers.user.social_auth.filter(provider='discord').first().uid}",
                })

            return JsonResponse({
                "dubbing": f"{episode.dubbing}",
                "name": episode.name,
                "name_full": f"{episode}",
                "sxex": episode.get_se(),
                "season": episode.season,
                "episode": episode.episode,
                "deadline": episode.deadline.timestamp(),
                "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'episode', 'obj_id': episode.id})}",
                "full_info": f"{EXTERNAL_URL}{reverse('stats_episode', kwargs={'episode_id': episode.id})}",
                "dubbers": dubbers,
            })

        elif type == "scene":
            scene = Scene.objects.filter(id=id).first()
            if scene is None:
                return JsonResponse({"error": "Scene not found"}, status=404)
            
            dubbers = []

            for s_dubbers in scene.usercharacterstable.all():
                dubbers.append({
                    "character_name": f"{s_dubbers.character}",
                    "user_id": f"{s_dubbers.user.social_auth.filter(provider='discord').first().uid}",
                })

            for s_dubbers in scene.usercharactertemporary.all():
                dubbers.append({
                    "character_name": f"{s_dubbers.name}",
                    "user_id": f"{s_dubbers.user.social_auth.filter(provider='discord').first().uid}",
                })

            return JsonResponse({
                "dubbing": f"{scene.dubbing}",
                "name": scene.name,
                "name_full": f"{scene}",
                "deadline": scene.deadline.timestamp(),
                "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'scene', 'obj_id': scene.id})}",
                "full_info": f"{EXTERNAL_URL}{reverse('stats_scene', kwargs={'scene_id': scene.id})}",
                "dubbers": dubbers,
            })
    
    except Exception as e:
        return JsonResponse({"error": f"There was an error while trying to het {type}: {e}"}, status=500)
    


    
@csrf_exempt
@require_GET_or_POST
@validate_token
def user_notification(request, id):
    discord_user = DiscordUser.objects.filter(discord_id=id).first()
    if discord_user is None:
        return JsonResponse({"error": "User was not found"}, status=404)

    if request.method == "POST":
        state_value = request.POST.get("state")
        if state_value is not None:
            state = state_value == "on"
            if discord_user.notification != state:
                discord_user.notification = state
                discord_user.save()

    return JsonResponse(data=discord_user.get_notification_data, status=200)


@csrf_exempt
@require_GET
@validate_token
def users_notification(request):
    return JsonResponse({"data": [discord_user.get_notification_data for discord_user in DiscordUser.objects.all()]}, status=200)


@csrf_exempt
@require_GET
@validate_token
def get_dubbings_characters(request):
    stable_characters = UserCharacterStable.objects.filter(done=False)
    temporary_characters = UserCharacterTemporary.objects.filter(done=False)

    data = []

    for stable_character in stable_characters:
        if stable_character.episode is not None:
            data.append({
                "dubbing": f"{stable_character.episode.dubbing}",
                "name": stable_character.episode.name,
                "name_full": f"{stable_character.episode}",
                "sxex": stable_character.episode.get_se(),
                "season": stable_character.episode.season,
                "episode": stable_character.episode.episode,
                "deadline": stable_character.episode.deadline.timestamp(),
                "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'episode', 'obj_id': stable_character.episode.id})}",
                "full_info": f"{EXTERNAL_URL}{reverse('stats_episode', kwargs={'episode_id': stable_character.episode.id})}",
                "character_name": f"{stable_character.character.name}",
                "user_id": stable_character.user.social_auth.filter(provider='discord').first().uid,
            })
            continue

        data.append({
            "dubbing": f"{stable_character.scene.dubbing}",
            "name": stable_character.scene.name,
            "name_full": f"{stable_character.scene}",
            "deadline": stable_character.scene.deadline.timestamp(),
            "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'scene', 'obj_id': stable_character.scene.id})}",
            "full_info": f"{EXTERNAL_URL}{reverse('stats_scene', kwargs={'scene_id': stable_character.scene.id})}",
            "character_name": f"{stable_character.character.name}",
            "user_id": stable_character.user.social_auth.filter(provider='discord').first().uid,
        })

    for temporary_character in temporary_characters:
        if temporary_character.episode is not None:
            data.append({
                "dubbing": f"{temporary_character.episode.dubbing}",
                "name": temporary_character.episode.name,
                "name_full": f"{temporary_character.episode}",
                "sxex": temporary_character.episode.get_se(),
                "season": temporary_character.episode.season,
                "episode": temporary_character.episode.episode,
                "deadline": temporary_character.episode.deadline.timestamp(),
                "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'episode', 'obj_id': temporary_character.episode.id})}",
                "full_info": f"{EXTERNAL_URL}{reverse('stats_episode', kwargs={'episode_id': temporary_character.episode.id})}",
                "character_name": f"{temporary_character.name}",
                "user_id": temporary_character.user.social_auth.filter(provider='discord').first().uid,
            })
            continue

        data.append({
            "dubbing": f"{temporary_character.scene.dubbing}",
            "name": temporary_character.scene.name,
            "name_full": f"{temporary_character.scene}",
            "deadline": temporary_character.scene.deadline.timestamp(),
            "script": f"{EXTERNAL_URL}{reverse('download_script', kwargs={'obj_type': 'scene', 'obj_id': temporary_character.scene.id})}",
            "full_info": f"{EXTERNAL_URL}{reverse('stats_scene', kwargs={'scene_id': temporary_character.scene.id})}",
            "character_name": f"{temporary_character.name}",
            "user_id": temporary_character.user.social_auth.filter(provider='discord').first().uid,
        })

    return JsonResponse({"data": data}, status=200)