"""
Environment configuration module for Django settings.
Handles loading and parsing environment variables with proper defaults.
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# 1. Resolve .env file location
# This finds the .env in the backend directory regardless of where you run the project from.
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'

# 2. Load environment variables
load_dotenv(dotenv_path=env_path)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()   
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE")

# 4. Database 
LOCAL_DB = os.getenv("LOCAL_DB")
SQLITE_DB = os.getenv("SQLITE_DB")
DOCKER_DB = os.getenv("DOCKER_DB")
PRODUCTION_DB = os.getenv("PRODUCTION_DB")

IS_DOCKER = os.path.exists('/.dockerenv') or os.getenv("RUNNING_ON_DOCKER", "false").lower() == "true"

if ENVIRONMENT == "production":
    DATABASE_URL = PRODUCTION_DB
elif IS_DOCKER:
    DATABASE_URL = DOCKER_DB
else:
    DATABASE_URL = LOCAL_DB

# 5. Core Application Settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# 6. Third Party Integrations
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Load and parse ALLOWED_ORIGINS

ALLOWED_HOSTS = (
    os.getenv("ALLOWED_HOSTS") or "localhost,127.0.0.1"
).split(",")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
