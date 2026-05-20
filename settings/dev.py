from dj_database_url import parse
import socket
from .base import *
import os

DEBUG = True
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1"]


# Load configuration from src.config
from src.config import (
    ALLOWED_ORIGINS, 
    ALLOWED_HOSTS, 
    DATABASE_URL,
    SECRET_KEY as CONFIG_SECRET_KEY,
)

# Use config values (SECRET_KEY from base is a default, override with env if needed)
SECRET_KEY = CONFIG_SECRET_KEY
ALLOWED_HOSTS = ALLOWED_HOSTS
ALLOWED_ORIGINS = ALLOWED_ORIGINS

DATABASES = {
    'default': parse(DATABASE_URL)
    # "default": parse(PRODUCTION_DB, conn_max_age=600)

}

STORAGES = {
    # Media: Goes to Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    
    # Static: Stays local (or use WhiteNoise in production)
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

