from . import paths
from ..config import SmartConfig
from .localization import LANGUAGES_KEYS

CONFIG:SmartConfig = SmartConfig(paths.CONFIG_PATH)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


SECRET_KEY = CONFIG.get('Django', 'secret_key', 'your-secret-key', description='Secret key to Django (change this to something unique)')

DJANGO_DEBUG = CONFIG.getboolean('Django', 'debug', fallback=False, description='Enables Django DEBUG logging')

DEBUG = DJANGO_DEBUG

LOGGING_DEBUG = CONFIG.getboolean('Logging', 'debug', fallback=False, description='Enables DEBUG logging')

ALLOWED_HOSTS = CONFIG.get('Networking', 'allowed_hosts', '*', description='List of allowed hosts separated by comma (",")').split(',')

LOCAL_ADDRESSES = CONFIG.get('Networking', 'local_addresses', 'localhost,127.0.0.1', description='List of local addresses separated by comma (",")').split(',')

TIME_ZONE = CONFIG.get('Django', 'tz', 'UTC', description='Django Timezone')

INSTANCE_NAME = CONFIG.get('Other', 'instance_name', 'Manager', description='Name of this instance. Displayed in tab.')

COMMUNITY_NAME = CONFIG.get('Other', 'community_name', 'Společenstvo dabignu', description='Name of the community.')

LANGUAGE_CODE = CONFIG.get('Localization', 'locale', 'en', description='Default language.', choices=LANGUAGES_KEYS)

EXTERNAL_URL = CONFIG.get('Networking', 'external_url', 'http://localhost', description='External URL.')
