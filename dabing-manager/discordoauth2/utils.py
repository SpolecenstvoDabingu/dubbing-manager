def get_discord_username_from_id(discord_id) -> str:
    from discord.models import DiscordUser
    return DiscordUser.objects.get(discord_id=discord_id) or "Unknown"