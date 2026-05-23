import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = os.environ.get("API_ID", "")
API_HASH = os.environ.get("API_HASH", "")
SESSION_NAME = os.environ.get("SESSION_NAME", "Ytuploadxbot")

CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

BOT_OWNER = os.environ.get("BOT_OWNER", "")
AUTH_USERS = os.environ.get("AUTH_USERS", "")

UPLOAD_MODE = os.environ.get("UPLOAD_MODE", "private")
VIDEO_TITLE_PREFIX = os.environ.get("VIDEO_TITLE_PREFIX", "")
VIDEO_TITLE_SUFFIX = os.environ.get("VIDEO_TITLE_SUFFIX", "")
VIDEO_DESCRIPTION = os.environ.get("VIDEO_DESCRIPTION", "")
VIDEO_CATEGORY = os.environ.get("VIDEO_CATEGORY", "")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

PORT = int(os.environ.get("PORT", 8080))
