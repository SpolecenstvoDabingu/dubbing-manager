from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .utils import validate_token, is_admin
from .models import DiscordUser
import json

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