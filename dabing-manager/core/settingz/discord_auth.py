from . import config

AUTHENTICATION_BACKENDS = [
    "social_core.backends.discord.DiscordOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

SOCIAL_AUTH_DISCORD_KEY = config.CONFIG.get('Discord', 'auth-key', 'your-auth-key', description='Auth key for Discord OAuth2')
SOCIAL_AUTH_DISCORD_SECRET = config.CONFIG.get('Discord', 'auth-secret', 'your-auth-secret', description='Auth secret for Discord OAuth2')
SOCIAL_AUTH_DISCORD_SCOPE = ["identify"]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'discordoauth2.pipeline.check_discord_whitelist',
    'discordoauth2.pipeline.create_user_if_not_exists',
    'discordoauth2.pipeline.associate_discord_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)