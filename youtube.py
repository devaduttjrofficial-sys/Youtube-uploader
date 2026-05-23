import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import config
import logging

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'client_secrets.json'

logger = logging.getLogger(__name__)


def create_client_secrets_file():
    if not os.path.exists(CREDENTIALS_FILE):
        client_secrets = {
            "installed": {
                "client_id": config.CLIENT_ID,
                "project_id": "youtube-uploader-bot",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": config.CLIENT_SECRET,
                "redirect_uris": [
                    "urn:ietf:wg:oauth:2.0:oob",
                    "http://localhost"]}}
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(client_secrets, f)


def get_auth_url():
    create_client_secrets_file()
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url


def authorize(auth_response_url):
    create_client_secrets_file()
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost'
    )
    flow.fetch_token(authorization_response=auth_response_url)
    credentials = flow.credentials
    with open(TOKEN_FILE, 'w') as f:
        f.write(credentials.to_json())
    return True


def get_authenticated_service():
    credentials = None
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(credentials.to_json())
        else:
            return None
    return build('youtube', 'v3', credentials=credentials)


def upload_video(file_path, title, description, category_id, privacy_status):
    youtube = get_authenticated_service()
    if not youtube:
        raise Exception("Not authorized. Please run /authorize first.")

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Uploaded {int(status.progress() * 100)}%")

    return response.get('id')


def set_thumbnail(video_id, thumbnail_path):
    youtube = get_authenticated_service()
    if not youtube:
        raise Exception("Not authorized.")

    request = youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path)
    )
    request.execute()


def upload_caption(video_id, caption_path, language="en", name="English"):
    youtube = get_authenticated_service()
    if not youtube:
        raise Exception("Not authorized.")

    body = {
        'snippet': {
            'videoId': video_id,
            'language': language,
            'name': name,
            'isDraft': False
        }
    }

    media = MediaFileUpload(caption_path, mimetype='application/octet-stream')
    request = youtube.captions().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    request.execute()
