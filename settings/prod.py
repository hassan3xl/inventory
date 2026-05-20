from .base import *
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

DEBUG = False

from src.config import (
    DATABASE_URL,
    SECRET_KEY,
    ALLOWED_HOSTS,
)
SECRET_KEY = SECRET_KEY

ALLOWED_HOSTS = ALLOWED_HOSTS.split(",") if ALLOWED_HOSTS else []


DATABASES = {

    "default": dj_database_url.config(DATABASE_URL)
}


# Free-tier friendly cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")


